import sys
import os
from datetime import datetime
# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.DebateAgent import DebateAgent
from debate.DebateManager import DebateManager


agent_prompts = {
    "Neutral American": "You are Bob, an American. You are participating in a debate on a political topic with Mike. Update your views on the topic based on both Mike's and John's responses.",
    "republican": "You are Mike, an American who supports the Republican party. You are participating in a debate on a political topic with Bob. Your goal is to convince Bob of your viewpoint.",
    "democratic": "You are John, an American who supports the Democratic party. You are participating in a debate on a political topic with Bob. Your goal is to convince Bob of your viewpoint.",
    "republican_2": "You are Mike, an American who supports the Republican party. You are participating in a debate on a political topic with Bob. Your goal is to convince Bob of your viewpoint. John is a Democrat, and your opposition. You may listen to their arguments and come up with a stronger argument to back yourself.",
    "democratic_2": "You are John, an American who supports the Democratic party. You are participating in a debate on a political topic with Bob. Your goal is to convince Bob of your viewpoint. Mike is a Republican, and your opposition. You may listen to their arguments and come up with a stronger argument to back yourself."
}


if __name__ == "__main__":
    model = "llama3.2:latest"
    debate_topics = {
        "gun_violence": "Should gun control laws be stricter in the United States?",
        "racism": "Is systemic racism a significant issue in America today?",
        "climate_change": "Should the US take stronger measures to combat climate change?",
        "illegal_immigration": "Should the US implement more lenient immigration policies?"
    }

    for topic_name, topic_question in debate_topics.items():
        agent1 = DebateAgent(name="Bob (Neutral American)", model=model, prompt=agent_prompts["Neutral American"])

        agent2 = DebateAgent(name="John (Democratic)", model=model, prompt=agent_prompts["democratic_2"])
        agent3 = DebateAgent(name="Mike (Republican)", model=model, prompt=agent_prompts["republican_2"])
    
        debate = DebateManager(agent1, agent2, topic_name, topic_question, agent3=agent3)
        debate.start(rounds=5)

        save_folder = "debate_transcripts"
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        debate.save_transcript(filename=f"./{save_folder}/{topic_name}_transcript_{timestamp}.json")