import sys
import os
import yaml

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.DebateAgent import DebateAgent
from debate.DebateManager import DebateManager

NUM_DEBATES = 10
if __name__ == "__main__":
    # load debate config
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debate_config.yaml")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    # ensure agent1 is neutral agent
    agent1 = DebateAgent(name="Sam", model=config["model"], affiliation={"leaning": None, "party": None}, age=None, gender=None)

    # create agents - NOTE: in future, could put this into YAML as well
    if config["debate_group"] == "neutral_republican":
        agents = [agent1, DebateAgent(name="Bob", model=config["model"], affiliation={"leaning": "conservative", "party": "Republican"}, age=None, gender=None)]

    elif config["debate_group"] == "neutral_democrat":
        agents = [agent1, DebateAgent(name="Mike", model=config["model"], affiliation={"leaning": "liberal", "party": "Democrat"}, age=None, gender=None)]

    elif config["debate_group"] == "neutral_republican_democrat":
        agents = [
            agent1,
            DebateAgent(name="Bob", model=config["model"], affiliation={"leaning": "conservative", "party": "Republican"}, age=None, gender=None),
            DebateAgent(name="Mike", model=config["model"], affiliation={"leaning": "liberal", "party": "Democrat"}, age=None, gender=None)
        ]
    else:
        raise ValueError("Invalid debate group")

    for topic in config["baseline_debate_topics"]: # + config["extra_debate_topics"]:
        dm = DebateManager(agents, topic, config["rounds"], config["debate_structure"], config["debate_group"])
        dm.start(NUM_DEBATES)
