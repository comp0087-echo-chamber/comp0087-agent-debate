import ollama

class DebateAgent:
    def __init__(self, name, model, affiliation):
        self.name = name
        self.model = model
        self.affiliation = affiliation
        self.label = f"{self.name} ({self.affiliation["party"]}, {self.affiliation["leaning"]})"

        self.debate_purpose = None
        self.prompt = None

    def generate_debate_purpose(self, topic, rounds, word_limit, other_agents):
        self.debate_purpose = f"You must try to convince the other agents: {', '.join(agent.label for agent in other_agents if agent != self)} that your views on {topic} are more valid than theirs, by taking part in a {rounds}-round structured debate. Output no more than {str(word_limit)} words"       

    def generate_prompt(self):
        self.prompt = f"You are {self.name}, a {self.affiliation['leaning']} American who supports the {self.affiliation['party']} party. {self.debate_purpose}"

    

    def respond(self, round_prompt, conversation):
        response = ollama.chat(
            model=self.model,
            options={"num_ctx": 4096, "temperature": 0.1},
            messages=[{"role": "user", "content": f"{self.prompt} {round_prompt} {conversation}"}]
        )

        return response["message"]["content"]
