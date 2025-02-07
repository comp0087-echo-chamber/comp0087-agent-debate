import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.DebateAgent import DebateAgent
from debate.DebateManager import DebateManager
from eval.Eval import Judge

if __name__ == "__main__":
    model = "llama3.2:3b"
<<<<<<< HEAD
    topic = "trade_tariffs"
=======
    topic = "evolution"
>>>>>>> 1c2a9c37930a8bb58f133774bc8111431d14d6f4
    word_limit = 75
    temperature = 0.5
    agent1 = DebateAgent(name= "Bob", model=model, affiliation={"leaning": "conservative", "party": "Republican"}, age="21", gender="male", temperature=temperature)
    agent2 = DebateAgent(name= "Mike", model=model,  affiliation={"leaning": "liberal", "party": "Democrat"}, age="21", gender="male", temperature=temperature)
    agent3 = DebateAgent(name= "Sam", model=model,  affiliation={"leaning": None, "party": None}, age="37", gender="Male", temperature=temperature)

    debate = DebateManager([agent1, agent2, agent3], topic, word_limit, rounds=2)

    debate.setup_agents()
    debate.start()