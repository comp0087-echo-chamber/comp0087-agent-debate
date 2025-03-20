import os
import sys
import yaml

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.DebateEvaluator import DebateEvaluator

if __name__ == "__main__":
    # load evaluation config from YAML
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_config.yaml")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    model = config["model"]
    debate_group = config["debate_group"]  # "neutral_republican", "neutral_democrat", or "neutral_republican_democrat"
    num_rounds = config["num_rounds"]
    use_scenarios = config["use_scenarios"]
    
    print(f"Selected debate group: {debate_group}")
    
    eval_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "debate", "eval_data")

    eval_data_path = os.path.join(eval_data_path, config["debate_group"], config["debate_structure"])

    # Likert scale is either: -3 to 3 OR 1 to 7
    # NOTE: so far, using the 1-7 scale seems to result in greater attitude variations
    
    debate_evaluator = DebateEvaluator(model, config["debate_group"], config["debate_structure"], config["num_rounds"], config["num_debates"], scale=config["scale"], evaluate_again=config["evaluate_again"])

    # transcripts_by_topic = [f for f in os.listdir(eval_data_path)]

    # for topic in transcripts_by_topic:
    #     topic_path = os.path.join(eval_data_path, topic)
    #     transcripts_in_topic = [f for f in os.listdir(topic_path)]

    #     for transcript in transcripts_in_topic:
    #         transcript_path =  os.path.join(topic_path, transcript)

    #         debate_evaluator.evaluate_transcript(transcript_path)


    # plot candle graphs    
    debate_evaluator.evaluate_debates(debate_transcripts_path=eval_data_path)
