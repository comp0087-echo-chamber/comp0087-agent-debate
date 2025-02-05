import sys
import os
from datetime import datetime
# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.DebateAgent import DebateAgent
from debate.DebateManager import DebateManager


if __name__ == "__main__":
    model = "llama3.2:3b"
    # model = "llama3.2:latest"

    debate_topics = {
        "gun_violence": "Should gun control laws be stricter in the United States?",
        "racism": "Is systemic racism a significant issue in America today?",
        "climate_change": "Should the US take stronger measures to combat climate change?",
        "illegal_immigration": "Should the US implement more lenient immigration policies?"
    }

    opinionated_agent = "democrat"
    opinionated_agent_name = "Mike" if opinionated_agent == "republican" else "John"

    agent_prompts = {
        "neutral": f"You are Bob, an American. You are participating in a debate on a political topic with {opinionated_agent_name}. Your goal is to listen to {opinionated_agent_name} and update your views on the topic based on his responses. Do not repeat points already mentioned by yourself in the conversation history.",
        "republican": "You are Mike, an American who supports the Republican Party. You are participating in a debate on a political topic with Bob. Your goal is to convince Bob of your viewpoint. Throughout the debate, you are firmly against the question being asked - do not change your view. Do not repeat points already mentioned by yourself in the conversation history.",
        "democrat": "You are John, an American who supports the Democratic Party. You are participating in a debate on a political topic with Bob. Your goal is to convince Bob of your viewpoint. Throughout the debate, you are firmly supportive the question being asked - do not change your view. Do not repeat points already mentioned by yourself in the conversation history.",
        "republican_2": "You are Mike, an American who supports the Republican party. You are participating in a debate on a political topic with Bob. Your goal is to convince Bob of your viewpoint. John is a Democrat, and your opposition. You may listen to their arguments and come up with a stronger argument to back yourself.",
        "democratic_2": "You are John, an American who supports the Democratic party. You are participating in a debate on a political topic with Bob. Your goal is to convince Bob of your viewpoint. Mike is a Republican, and your opposition. You may listen to their arguments and come up with a stronger argument to back yourself."
    }

    for topic_name, topic_question in debate_topics.items():
        agent1 = DebateAgent(name="Bob (Neutral American)", model=model, prompt=agent_prompts["neutral"])

        if opinionated_agent == "republican":
            agent2 = DebateAgent(name="Mike (Republican)", model=model, prompt=agent_prompts["republican"])
        else:
            agent2 = DebateAgent(name="John (Democrat)", model=model, prompt=agent_prompts["democrat_2"])
        # agent3 = DebateAgent(name="Mike (Republican)", model=model, prompt=agent_prompts["republican_2"])
    
        debate = DebateManager(agent1, agent2, topic_name, topic_question)
        debate.start(rounds=10)

        save_folder = f"debate_transcripts_{opinionated_agent}"
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # debate.save_transcript(filename=f"./{save_folder}/{topic_name}_transcript_{timestamp}.json")
        debate.save_transcript(filename=f"./{save_folder}/{topic_name}_transcript.json")
