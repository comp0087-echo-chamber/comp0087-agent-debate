import sys
import os
import yaml
import json
from datetime import datetime
from Comparison import generate_evaluations, compute_anova, compute_levenes_test, save_comparison_results

# Load config
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comparison_config.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

COMPARE_PATH = config["compare_path"]
DEBATE_GROUP = config["debate_group"]
DEBATE_STRUCTURE = config["debate_structure"]
NUM_DEBATES = config["num_debates"]

def collect_evaluations():
    """
    Dynamically detects variations (e.g., opinionated_male, opinionated_female)
    and collects means & IQRs **by round** for each topic.

    Returns a dictionary mapping:
    topic -> {variation_1: {"mean_of_means": [...], "mean_of_iqrs": [...]}, variation_2: {...}, ...}
    """
    evaluations = {}

    # Detect variations (e.g., opinionated_male, opinionated_female)
    variations = [
        var for var in os.listdir(COMPARE_PATH)
        if os.path.isdir(os.path.join(COMPARE_PATH, var))
    ]
    
    print(f"Detected variations for comparison: {variations}")

    for variation in variations:
        variation_path = os.path.join(COMPARE_PATH, variation, DEBATE_GROUP, DEBATE_STRUCTURE)

        if not os.path.exists(variation_path):
            print(f"Warning: {variation_path} does not exist.")
            continue
        
        for topic in os.listdir(variation_path):  # e.g., climate_change, gun_violence
            topic_path = os.path.join(variation_path, topic)

            # Generate evaluations.json if it doesn't exist
            evaluations_file = generate_evaluations(topic_path, NUM_DEBATES)

            if not os.path.isdir(topic_path) or not os.path.exists(evaluations_file):
                continue

            # Load evaluations.json
            with open(evaluations_file, "r") as file:
                topic_evals = json.load(file)

            # Ensure topic exists in evaluations dict
            if topic not in evaluations:
                evaluations[topic] = {var: {"mean_of_means": [], "mean_of_iqrs": []} for var in variations}

            # Extract means & IQRs for all agent types
            for agent_type in ["neutral", "republican", "democrat"]:
                evaluations[topic][variation]["mean_of_means"].extend(topic_evals[topic][agent_type]["mean_of_means"])
                evaluations[topic][variation]["mean_of_iqrs"].extend(topic_evals[topic][agent_type]["mean_of_iqrs"])

    return evaluations


if __name__ == "__main__":
    print(f"Starting comparison for {DEBATE_GROUP} ({DEBATE_STRUCTURE})")

    # Collect evaluations across variations
    evaluations = collect_evaluations()

    # Run ANOVA & Levene’s test across all detected variations
    anova_results = compute_anova(evaluations)
    levene_results = compute_levenes_test(evaluations)

    # Save overall comparison results
    save_comparison_results(anova_results, levene_results, COMPARE_PATH)

    print("Comparison completed.")
