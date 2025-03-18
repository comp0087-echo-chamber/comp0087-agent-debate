import sys
import os
import yaml
from datetime import datetime
import multiprocessing

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.DebateAgent import DebateAgent
from debate.DebateManager import DebateManager


def run_debate_for_topic(topic, debate_scenario=None, debate_question=None, eval_prompt=None):

    print(f"Starting debate for topic: {topic}")

    # Load config inside the function (to prevent multiprocessing issues)
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debate_config.yaml")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    names = {"Male": ["Bob", "Mike", "James"],"Female": ["Sarah", "Stephanie", "Emily"], "Gender-Neutral": ["Sam", "Alex", "Taylor"]}
    used_names = set()

    def get_name(gender):
        available_names = [name for name in names.get(gender, names["Gender-Neutral"]) if name not in used_names]
        if available_names:
            chosen_name = available_names[0]
            used_names.add(chosen_name)
            return chosen_name

    # Ensure agent1 is a neutral agent
    agent1 = DebateAgent(name=get_name(config["agents"]["neutral"]["gender"]), model=config["agents"]["neutral"]["model"], affiliation={"leaning": None, "party": None}, age=config["agents"]["neutral"]["age"], gender=config["agents"]["neutral"]["gender"], word_limit=config["word_limit"])

    # Create agents based on the config
    if config["debate_group"] == "neutral_republican":
        agents = [agent1, DebateAgent(name= get_name(config["agents"]["republican"]["gender"]), model=config["agents"]["republican"]["model"], affiliation={"leaning": "conservative", "party": "Republican"}, age=config["agents"]["republican"]["age"], gender=config["agents"]["republican"]["gender"], word_limit=config["word_limit"])]


    elif config["debate_group"] == "neutral_democrat": 
        agents = [agent1, DebateAgent(name= get_name(config["agents"]["democrat"]["gender"]), model=config["agents"]["democrat"]["model"], affiliation={"leaning": "liberal", "party": "Democrat"}, age=config["agents"]["democrat"]["age"], gender=config["agents"]["democrat"]["gender"], word_limit=config["word_limit"])]

    elif config["debate_group"] == "neutral_republican_democrat":
        agents = [
            agent1,
            DebateAgent(name= get_name(config["agents"]["republican"]["gender"]), model=config["agents"]["republican"]["model"], affiliation={"leaning": "conservative", "party": "Republican"}, age=config["agents"]["republican"]["age"], gender=config["agents"]["republican"]["gender"], word_limit=config["word_limit"]),
            DebateAgent(name= get_name(config["agents"]["democrat"]["gender"]), model=config["agents"]["democrat"]["model"], affiliation={"leaning": "liberal", "party": "Democrat"}, age=config["agents"]["democrat"]["age"], gender=config["agents"]["democrat"]["gender"], word_limit=config["word_limit"])
        ]
    else:
        raise ValueError("Invalid debate group")

    # Run the debate for this topic
    dm = DebateManager(agents, topic, debate_scenario, debate_question, eval_prompt, config["num_rounds"], config["debate_structure"], config["debate_group"], config["use_extended_personas"])
    dm.start(config["num_debates"])

    print(f"Debate completed for topic: {topic}")

if __name__ == "__main__":
    # Load debate config
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debate_config.yaml")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    # Get topics from command-line arguments or from config
    if len(sys.argv) > 1:
        topics = sys.argv[1:]
    else:
        topics = config["baseline_debate_topics"]
    
    print(f"Running debates for topics: {topics}")
    start_time = datetime.now()

    if config["use_multiprocessing"]:

        # Use multiprocessing to parallelize by topic
        num_workers = min(len(topics), multiprocessing.cpu_count())  # Limits max parallel topics
        with multiprocessing.Pool(processes=num_workers) as pool:
            pool.map(run_debate_for_topic, topics)
    
    else:
        if config["use_scenarios"]:
            debate_scenarios = config["baseline_debate_scenarios"]
            debate_questions = config["baseline_debate_questions"]
            eval_prompts = config["eval_prompts"]
            for scenario, question, eval_prompt in zip(debate_scenarios, debate_questions, eval_prompts):
                run_debate_for_topic(None, scenario, question, eval_prompt)
        else:
            for topic in topics:
                run_debate_for_topic(topic)


    print("All debates completed")
    print(f"That took {(datetime.now() - start_time).total_seconds():.2f} seconds")

