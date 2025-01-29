import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.DebateAgent import DebateAgent
from debate.DebateManager import DebateManager

if __name__ == "__main__":
    agent1 = DebateAgent(name= "Bob (Republican)", model="llama3.2:3b", prompt="You are an American who supports the Republican party")
    agent2 = DebateAgent(name= "Mike (Democrat)", model="llama3.2:3b", prompt="You are an American who supports the Democrat Party")
    topic = "Economic Policy"

    debate = DebateManager(agent1, agent2, topic)
    debate.start()