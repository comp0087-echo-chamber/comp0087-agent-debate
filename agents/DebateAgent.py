import ollama
from openai import OpenAI
from dotenv import load_dotenv
import os
import re
load_dotenv()  
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

# TODO: Update all agent prompts based on prompting used in prev multiagent debate papers

class DebateAgent:
    def __init__(self, name, model, affiliation, age, gender,  word_limit, temperature=None):
        self.name = name
        self.model = model
        self.affiliation = affiliation
        self.age = age
        self.gender = gender
        self.label = f"{self.name} ({self.affiliation['party']}, {self.affiliation['leaning']}, {self.age}, {self.gender})"
        self.debate_purpose = None
        self.prompt = None
        self.temperature = temperature
        self.word_limit = word_limit

    def get_agent_details(self):
        details = [self.name]
        party = self.affiliation.get("party")
        details.append(party if party else "Neutral")

        if self.gender:
            details.append(self.gender)
        if self.age:
            details.append(str(self.age))

        return ", ".join(details)

    def generate_debate_purpose(self, topic, rounds, other_agents):
        self.debate_purpose = ""
        if "deepseek-r1" in self.model:
            self.debate_purpose += "After your reasoning, before writing your response, use the phrase 'My response:' exactly. "
        if self.affiliation["leaning"] == None:

            # NOTE: when given the num rounds in debate `{rounds}-round` agents sometimes repond like this for current prompt: "Bob, Republican > I cannot participate in a debate that will be used to promote a specific political agenda. Is there something else I can help you with?"
            self.debate_purpose += f"This is a debate about {topic}. Your goal is to listen to the other agent(s). Keep your reply shorter than {str(self.word_limit)} words. Do not repeat points already mentioned by yourself in the conversation history."
        else:
            self.debate_purpose += f"This is a debate about {topic}. Your goal is to convince the other agent(s) of your position. Keep your reply shorter than {str(self.word_limit)} words. Do not repeat points already mentioned by yourself in the conversation history."

    def generate_prompt(self):
        party_support = f" who supports the {self.affiliation['party']} party" if self.affiliation['party'] != None else ""

        self.prompt = f"You are {self.name}," \
            f"{f' a {self.age} year old' if self.age else ''}" \
            f"{f' {self.gender}' if self.gender else ''}" \
            f" {self.affiliation['leaning'] if self.affiliation['leaning'] else 'an'} American{party_support}. \n" \
            f"{self.debate_purpose}"


    def respond(self, debate_phase_prompt, conversation):
        if "gpt" in self.model:
            completion = client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=[
                {"role": "user", "content":f"{self.prompt} \n{debate_phase_prompt if debate_phase_prompt != None else ''} \n{conversation}"}
            ],
            )
            response= completion.choices[0].message.content
            return response
        
        else:
            response = ollama.chat(
                model=self.model,
                options={"num_ctx": 4096, "temperature": 0.1},
                messages=[{"role": "user", "content": f"{self.prompt} \n{debate_phase_prompt if debate_phase_prompt != None else ''} \n{conversation}"}]  # TODO: Say Conversation History?
            )
        
        if "deepseek-r1" in self.model:
            response = re.sub(r"<think>.*?</think>", "", response["message"]["content"].split("My response:")[-1].strip(), flags=re.DOTALL).strip()
            return self.reduce_response_size(response)

        return self.reduce_response_size(response["message"]["content"])
    
    def reduce_response_size(self,response):
        words = re.findall(r'\S+', response)  # Split response into words while preserving punctuation
        if len(words) > self.word_limit:
            trimmed_response = " ".join(words[-self.word_limit:])  # Keep the last word_limit words
        else:
            trimmed_response = response  # No trimming needed if within limit

        return trimmed_response.strip()
    
    
