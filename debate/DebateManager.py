import ollama

class DebateManager:

    def __init__(self, agent1, agent2, topic):
        self.agent1 = agent1
        self.agent2 = agent2
        self.topic = topic
        self.conversation = f"We will be discussing {topic}"

    def print_response(self, response):
        print(response)

    def debate_round(self, agent):
        response = f"{agent.name} > {agent.respond(self.conversation)} \n"
        self.conversation += response
        self.print_response(response)

    def start(self):
        self.debate_round(self.agent1)
        self.debate_round(self.agent2)
        self.debate_round(self.agent1)
        self.debate_round(self.agent2)

