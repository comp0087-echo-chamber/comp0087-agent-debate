import os
import json
from datetime import datetime

# TODO: Work on combining eval data into debate transcription
# to avoid saving two copies of the agents' responses (or vice versa)

# TODO: Update structured debate prompts in line with debate prompts in prev papers


class DebateManager:

    def __init__(self, agents, topic, rounds, debate_structure, debate_group):
        self.topic = topic
        self.agents = agents
        self.rounds = rounds
        self.debate_structure = debate_structure
        self.debate_group = debate_group  # used for filenames when saving files

        self.data_for_evaluation = {  # used for evaluation
            "topic": self.topic,
            "neutral": {},
            "republican": {},
            "democrat": {}
        }

        self.ordered_conversation_history = []  # conversation history to pass to agents
        self.conversation_for_transcription = []

        self.round_num_counts = {"neutral": 0, "democrat": 0, "republican": 0}


    def _print_response(self, agent_details, response):
        print(f"{agent_details} > {response}")


    def generate_agent_prompts(self):
        for agent in self.agents:
            agent.generate_debate_purpose(self.topic, self.rounds, self.agents)

        for agent in self.agents:
            agent.generate_prompt()
            print(agent.prompt, "\n")


    def debate_round(self, agent, debate_phase_prompt=None):

        conversation = "\n".join(self.ordered_conversation_history)
        response = agent.respond(debate_phase_prompt, conversation)
        self._print_response(agent.get_agent_details(), response)

        # update data related to convo history for transcribing & evaluation
        self.ordered_conversation_history.append(f"{agent.name}: {response}")
        self.conversation_for_transcription.append({"agent": agent, "response": response})

        agent_type = agent.affiliation['party'].lower() if agent.affiliation['party'] != None else "neutral"
        round_num = self.round_num_counts[agent_type]
        self.data_for_evaluation[agent_type][f"round_{round_num}"] = response
        self.round_num_counts[agent_type] += 1


    def start(self):
        self.generate_agent_prompts()

        if self.debate_structure == "structured":
            self.start_structured_debate()
        else:
            self.start_unstructured_debate()

        self.save_debate_transcription()
        self.save_evaluation_data()


    def start_structured_debate(self):
        for agent in self.agents:
            # self.debate_round(agent, "Present your opening opinions on the topic. Do not rebut the other agent. Do not disagree with them.")
            self.debate_round(agent, "Present your opening opinions on the topic.")

        for _ in range(1, self.rounds+1): 
            for agent in self.agents:
                # self.debate_round("Please rebut the other agent's opinions and continue to argue your own.", agent)
                self.debate_round(agent, "Complete your next reply.")  # NOTE: This takes the prompt used in baseline paper

        if self.rounds > 1: 
            for agent in self.agents:
                # self.debate_round(agent, "Please rebut the other agent's opinions, and give closing arguments. If you wish to change your position to align or diverge with your fellow agents, please do so.")
                self.debate_round(agent, "Give your closing arguments on the topic.")


    def start_unstructured_debate(self):
        for _ in range(self.rounds):
            self.debate_round(self.agents[1], "Complete your next reply.")  # opinionated agent starts the debate

            if len(self.agents) > 2:  # if there are 3 agents, let 3rd agent speak
                self.debate_round(self.agents[2], "Complete your next reply.")

            self.debate_round(self.agents[0], "Complete your next reply.")


    def save_evaluation_data(self):
        timestamp = datetime.now().strftime('%H_%M_%S')
        save_folder = f"eval_data/{self.debate_group}/{self.debate_structure}/{self.topic.replace(' ', '_')}"
        os.makedirs(save_folder, exist_ok=True)
        filename = f"{save_folder}/transcript_{timestamp}.json"
    
        with open(filename, "w") as file:
            json.dump(self.data_for_evaluation, file, indent=4)

        print(f"Evaluation data saved:\n- {filename}")


    def save_debate_transcription(self):
        timestamp = datetime.now().strftime('%H_%M_%S')

        save_folder = f"debate_transcripts/{self.debate_group}/{self.debate_structure}/{self.topic.replace(' ', '_')}"
        os.makedirs(save_folder, exist_ok=True)

        # TXT
        text_filename = f'{save_folder}/transcript_{timestamp}.txt'
        with open(text_filename, 'w') as f:
            for round in self.conversation_for_transcription:
                f.write(f'{round["agent"].label} > {round["response"]} \n\n')

        # JSON
        json_filename = f'{save_folder}/transcript_{timestamp}.json'
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
                        "response": round["response"]}
                for round in self.conversation_for_transcription
            ]
        }

        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f)

        print(f"Transcripts saved:\n- {text_filename}\n- {json_filename}")
