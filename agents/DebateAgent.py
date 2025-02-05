import ollama

class DebateAgent:
    def __init__(self, name, model, affiliation, age, gender):
        self.name = name
        self.model = model
        self.affiliation = affiliation
        self.age = age
        self.gender = gender
        self.label = f"{self.name} ({self.affiliation['party']}, {self.affiliation['leaning']}, {self.age}, {self.gender})"
        self.debate_purpose = None
        self.prompt = None

    def generate_debate_purpose(self, topic, rounds, word_limit, other_agents):
        if self.affiliation["leaning"] == "":
            self.debate_purpose = f"You must consider what the other agents : {', '.join(agent.label for agent in other_agents if agent != self)} are discussing on the topic of {topic}  in a {rounds}-round structured debate. Please consider what the other agents are discussing, and how it may align with your views, and if you feel that they make sensible points, please consider changing your position. Output no more than {str(word_limit)} words."       
        else:
            self.debate_purpose = f"You must try to convince the other agents: {', '.join(agent.label for agent in other_agents if agent != self)} that your views on {topic} are more valid than theirs, by taking part in a {rounds}-round structured debate. Do not allow yourself to have your posiiton changed. Output no more than {str(word_limit)} words."       

    def generate_prompt(self):
        party_support = f"who supports the {self.affiliation['party']} party" if self.affiliation['party'] != "neutral" else ""
        self.prompt = f"You are {self.name}, a {self.age} year old, {self.gender}, {self.affiliation['leaning']} American {party_support}. {self.debate_purpose}"
        # self.prompt = f"You are {self.name}, a {self.age} year old, {self.gender}, {self.affiliation['leaning']} American {f"who supports the {self.affiliation['party']} party" if self.affiliation['party']!= "neutral" else ""}. {self.debate_purpose}"

    def respond(self, round_prompt, conversation):
        response = ollama.chat(
            model=self.model,
            options={"num_ctx": 4096, "temperature": 0.1},
            messages=[{"role": "user", "content": f"{self.prompt} {round_prompt} {conversation}"}]
        )

        return response["message"]["content"]
