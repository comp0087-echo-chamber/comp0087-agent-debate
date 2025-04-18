import ollama
from openai import OpenAI
from dotenv import load_dotenv
import os
import re
import json
load_dotenv()  
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

# TODO: Update all agent prompts based on prompting used in prev multiagent debate papers

class DebateAgent:
    def __init__(self, name, identifier, model, affiliation, age, gender,  word_limit, temperature, know_other_agents=False):
        self.name = name
        self.identifier = identifier
        self.model = model
        self.affiliation = affiliation
        self.age = age
        self.gender = gender
        self.label = f"{self.name} ({self.affiliation['party']}, {self.affiliation['leaning']}, {self.age}, {self.gender})"
        self.debate_purpose = None
        self.prompt = None
        self.temperature = temperature
        self.word_limit = word_limit
        self.know_other_agents = know_other_agents

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
            self.debate_purpose += f"This is a debate about {topic}. Your goal is to listen to the other agent(s). Keep your reply shorter than {str(self.word_limit)} words. Do not repeat points already mentioned by yourself or others in the conversation history."
        else:
            self.debate_purpose += f"This is a debate about {topic}. Your goal is to convince the other agent(s) of your position. Keep your reply shorter than {str(self.word_limit)} words. Do not repeat points already mentioned by yourself or others in the conversation history."

    def generate_debate_purpose_with_scenario(self, topic, debate_scenario, debate_question, rounds, agents):
        self.debate_purpose = f"This is a debate about {topic}. "
        self.debate_purpose += f"We consider a scenario: \n{debate_scenario}\n"
        self.debate_purpose += f"In your responses, please answer the following question: {debate_question}\n"

        if self.know_other_agents:
            # tell the other agents the genders of who they are debating with
            self.debate_purpose += "You are debating with "

            agent_descriptions = []
            for agent in agents:
                if agent.name != self.name:  # Exclude self from the list
                    gender_label = "an American man" if agent.gender == "male" else "an American woman" if agent.gender == "female" else "an American"
                    agent_descriptions.append(f"{agent.name}, {gender_label}")

            self.debate_purpose += " and ".join(agent_descriptions) + ". "
       
        if "deepseek-r1" in self.model:
            self.debate_purpose += "After your reasoning, before writing your response, use the phrase 'My response:' exactly. "
        if self.affiliation["leaning"] == None:

            # NOTE: when given the num rounds in debate `{rounds}-round` agents sometimes repond like this for current prompt: "Bob, Republican > I cannot participate in a debate that will be used to promote a specific political agenda. Is there something else I can help you with?"
            self.debate_purpose += f"Your goal is to listen to the other agent(s). Keep your reply shorter than {str(self.word_limit)} words. YOU MUST not repeat points already mentioned by yourself or others in the conversation history."
        else:
            self.debate_purpose += f"Your goal is to convince the other agent(s) of your position. Keep your reply shorter than {str(self.word_limit)} words. YOU MUST not repeat points already mentioned by yourself or others in the conversation history."

    def load_extended_personas(self):
        persona_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extended_personas.json")
        try:
            with open(persona_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading persona file: {e}")
            return {}

    def generate_prompt(self, use_extended_personas):

        if not use_extended_personas:
            party_support = f" who supports the {self.affiliation['party']} party" if self.affiliation['party'] != None else ""

            self.prompt = f"You are {self.name}," \
                f"{f' a {self.age} year old' if self.age else ''}" \
                f"{f' {self.gender}' if self.gender else ''}" \
                f" {self.affiliation['leaning'] if self.affiliation['leaning'] else 'an'} American{party_support}. \n" \
                f"{self.debate_purpose}"
        else:
            extended_personas = self.load_extended_personas().get("generated_personas")

            if self.affiliation['party'] == None:
                agent_type = "neutral"
            else:
                agent_type = self.affiliation['party'].lower()

            if not self.gender and not self.age:
                self.prompt =  extended_personas.get(self.identifier).get("baseline")
            elif self.age:
                self.prompt = extended_personas.get(self.identifier, {}).get("age").get(str(self.age))
            elif self.gender:
                self.prompt = extended_personas.get(self.identifier, {}).get("gender").get(str(self.gender.lower()))

            if self.prompt != None:
                if self.debate_purpose != None:
                    self.prompt += f"\n{self.debate_purpose}"
            else:
                raise TypeError("An age has been assigned to the gender attribute in the config file (or vice versa).")

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
            response = ollama.generate(
                model=self.model,
                options={"num_ctx": 8192, "temperature": self.temperature},
                prompt=f"{self.prompt} \n{debate_phase_prompt if debate_phase_prompt != None else ''} \n{conversation}"  # TODO: Say Conversation History?
            )
        
        if "deepseek-r1" in self.model:
            raw_response = response.response
            cleaned_response = re.sub(
                r"<think>.*?</think>",
                "",
                raw_response.split("My response:")[-1].strip(),
                flags=re.DOTALL
            ).strip()
            return self.reduce_response_size(cleaned_response)
        
        return self.reduce_response_size(response["response"])
    
    def reduce_response_size(self,response):
        words = re.findall(r'\S+', response)  # Split response into words while preserving punctuation
        if len(words) > self.word_limit:
            trimmed_response = " ".join(words[-self.word_limit:])  # Keep the last word_limit words
        else:
            trimmed_response = response  # No trimming needed if within limit

        return trimmed_response.strip()
    
    
