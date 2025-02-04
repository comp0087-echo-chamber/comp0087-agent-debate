import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.DebateAgent import DebateAgent
from debate.DebateManager import DebateManager

if __name__ == "__main__":
    model = "llama3.2:3b"
    debate_topics = {
        "gun_violence": "Should gun control laws be stricter in the United States?",
        "racism": "Is systemic racism a significant issue in America today?",
        "climate_change": "Should the US take stronger measures to combat climate change?",
        "illegal_immigration": "Should the US implement more lenient immigration policies?"
    }

    for topic_name, topic_question in debate_topics.items():
        agent1 = DebateAgent(name="Bob (Neutral American)", model=model, prompt="You are Bob, an American. You are participating in a debate on a political topic with Mike. Your goal is listen to Mike and update your views on the topic based on his responses. Avoid repeating points already mentioned by yourself in the conversation history.")

        agent2 = DebateAgent(name="Mike (Republican)", model=model, prompt="You are Mike, an American who supports the Republican party. You are participating in a debate on a political topic with Bob. Your goal is to convince Bob of your viewpoint. Throughout the debate, you are firmly against the question being asked - do not change your view. Avoid repeating points already mentioned by yourself in the conversation history.")
    
        debate = DebateManager(agent1, agent2, topic_name, topic_question)
        debate.start(rounds=10)

        save_folder = "debate_transcripts"
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        debate.save_transcript(filename=f"./{save_folder}/{topic_name}_transcript.json")
