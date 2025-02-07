import ollama
from eval.Eval import Eval
from datetime import datetime
import json
import os

class DebateManager:

    def __init__(self, agents, topic, word_limit, rounds):
        self.topic = topic
        self.possible_topics = {"gun_crime":"gun crime", "abortion":"abortion", "illegal_immigration": "illegal immigration", "trade_tariffs": "trade tariffs", "the_sky": "what colour is the sky", "evolution": "evolution", "climate_change": "climate change"}
        self.agents = agents
        self.rounds = rounds
        self.word_limit = word_limit
        self.conversation = []
        self.conversation_text = f""
        self.word_limit
        self.eval = Eval()

    def print_response(self, response):
        print(response)

    def debate_round(self, round_prompt, agent):
        conversation = self.get_conversation()
        response = agent.respond(round_prompt, conversation)
        self.conversation.append({"agent": agent, "response": response})

        response_text = f"{agent.label} > {response} \n"

        # Incorporate eval

        self.conversation_text += response_text
        self.print_response(response_text)

    def get_conversation(self):
        # return " \n ".join(map(lambda round: f"{round["agent"].label} > {round["response"]} \n", self.conversation))
        return " \n ".join(map(lambda rnd: f"{rnd['agent'].label} > {rnd['response']} \n", self.conversation))


    def setup_agents(self):
        # Setup all of the agents by giving them the topic, their prompt and the debate structure, as well as naming and defining the other agents they will debate against
        for agent in self.agents:
            agent.generate_debate_purpose(self.possible_topics[self.topic], self.rounds, self.word_limit, self.agents)

        for agent in self.agents:
            agent.generate_prompt()
            print(agent.prompt, "\n")

    def transcribe_debate(self):
        timestamp = datetime.now().strftime('%H_%M_%S')
        # TXT
        os.makedirs(f'debate_transcripts/{self.topic}', exist_ok=True)
        text_filename = f'debate_transcripts/{self.topic}/transcript_{timestamp}.txt'
        with open(text_filename, 'w') as f:
            for round in self.conversation:
                f.write(f'{round["agent"].label} > {round["response"]} \n\n')

        # JSON
        json_filename = f'debate_transcripts/{self.topic}/transcript_{timestamp}.json'
        json_data = {
            "topic": self.topic,
            "timestamp": timestamp,
            "agents": [ {
                "agent_id": index,
                "name": agent.name,
                "leaning": agent.affiliation["leaning"], 
                "party": agent.affiliation["party"], 
                "age": agent.age, 
                "gender":  agent.gender
            } for index, agent in enumerate(self.agents)],
            "rounds": [
                    {
                        "agent_id": self.agents.index(round["agent"]),
                        "response": round["response"], 
                        "attitude": self.eval.eval(round["response"])}
                for round in self.conversation
            ]
        }

        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f)

        print(f"Transcripts saved:\n- {text_filename}\n- {json_filename}")
        


    def start(self):
        # Round 1
        
        for agent in self.agents:
            self.debate_round("Present your opening opinions on the topic. Do not rebutt the other agent. Do not disagree with them.",  agent)

        for agent in self.agents:
            self.debate_round("Please rebutt the other agent's opinions and continue to argur your own.",  agent)

        for agent in self.agents:
            self.debate_round("Please rebutt the other agent's opinions, and give closing arguments. If you wish to change your position to align or diverge with your fellow agents please do so,",  agent)

            
        self.transcribe_debate()
