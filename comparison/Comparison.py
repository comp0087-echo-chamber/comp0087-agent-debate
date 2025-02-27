import os
import json
import numpy as np
import scipy.stats as stats

def generate_evaluations(topic_path, num_debates):
    """
    Generates evaluations.json by extracting mean attitude scores & IQR for each debate group.
    """
    evaluations = {}

    # Load all transcripts for this topic
    transcripts = sorted([f for f in os.listdir(topic_path) if f.endswith(".json") and f != "evaluations.json"])[:num_debates]

    if not transcripts:
        print(f"No transcripts found in {topic_path}")
        return None

    for transcript in transcripts:
        transcript_path = os.path.join(topic_path, transcript)
        
        with open(transcript_path, "r") as file:
            data = json.load(file)

        topic = data["topic"].replace(" ","_")
        if topic not in evaluations:
            evaluations[topic] = {}

        for group, scores in data["attitude_scores"].items():
            if group not in evaluations[topic]:
                evaluations[topic][group] = {"means": [], "iqrs": []}

            mean_score = np.mean(scores)
            iqr_score = stats.iqr(scores)  # Interquartile Range
            evaluations[topic][group]["means"].append(mean_score)
            evaluations[topic][group]["iqrs"].append(iqr_score)

    # Save evaluations.json
    eval_file = os.path.join(topic_path, "evaluations.json")
    with open(eval_file, "w") as file:
        json.dump(evaluations, file, indent=4)

    print(f"Saved evaluations to {eval_file}")
    return eval_file

def compute_anova(evaluations):
    """Run one-way ANOVA on attitude score means for each topic across variations."""
    
    anova_results = {}

    for topic, variation_data in evaluations.items():
        means_groups = [variation["means"] for variation in variation_data.values()]

        # Ensure we have at least two groups to compare
        if len(means_groups) < 2:
            print(f"Skipping ANOVA for {topic}, not enough variations.")
            continue

        # Run ANOVA
        f_stat, p_value = stats.f_oneway(*means_groups)

        # Store results
        anova_results[topic] = {"f_stat": f_stat, "p_value": p_value}

    return anova_results


def compute_levenes_test(evaluations):
    """Run Levene’s test on IQRs for each topic across variations."""
    
    levene_results = {}

    for topic, variation_data in evaluations.items():
        iqr_groups = [variation["iqrs"] for variation in variation_data.values()]

        # Ensure we have at least two groups to compare
        if len(iqr_groups) < 2:
            print(f"Skipping Levene's test for {topic}, not enough variations.")
            continue

        # Run Levene’s test
        f_stat, p_value = stats.levene(*iqr_groups)

        # Store results
        levene_results[topic] = {"f_stat": f_stat, "p_value": p_value}

    return levene_results


def save_comparison_results(anova_results, levene_results, topic_path):
    """
    Saves ANOVA & Levene’s test results in comparison_results.json.
    """
    results = {
        "comparison": topic_path.split("/")[-1],
        "anova": anova_results,
        "levenes": levene_results
    }

    result_file = os.path.join(topic_path, "comparison_results.json")
    with open(result_file, "w") as file:
        json.dump(results, file, indent=4)

    print(f"Saved comparison results to {result_file}")
