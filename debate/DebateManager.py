import json


class DebateManager:

    def __init__(self, agent1, agent2, topic):
        self.agent1 = agent1
        self.agent2 = agent2
        self.topic = topic
        self.debate_data = {  # used for evaluation
            "topic": topic,
            "neutral": {},
            "republican": {}
        }
        self.ordered_debate_history = [topic]  # incrementally build debate log to give agents
        self.neutral_turn_count = 1
        self.republican_turn_count = 1

    def print_response(self, agent_name, response):
        print(f"{agent_name} > {response}")

    def debate_round(self, agent):
        agent_key = "neutral" if agent.name == "Bob (Neutral American)" else "republican"

        conversation_history = "\n".join(self.ordered_debate_history)
        response = agent.respond(conversation_history)  

        if agent_key == "neutral":
            self.debate_data[agent_key][f"turn {self.neutral_turn_count}"] = response
            self.neutral_turn_count += 1
        else:
            self.debate_data[agent_key][f"turn {self.republican_turn_count}"] = response
            self.republican_turn_count += 1

        self.ordered_debate_history.append(f"{agent.name}: {response}")
        self.print_response(agent.name, response)

    def start(self, rounds=5):
        for _ in range(rounds):
            self.debate_round(self.agent2)  # opinionated agent start the debate
            self.debate_round(self.agent1)

    def save_transcript(self, filename):
        with open(filename, "w") as file:
            json.dump(self.debate_data, file, indent=4)
