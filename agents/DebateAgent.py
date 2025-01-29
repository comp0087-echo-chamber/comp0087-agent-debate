import ollama

class DebateAgent:
    def __init__(self, name, model, prompt):
        self.name = name
        self.model = model
        self.prompt = prompt

    def respond(self, input_message):
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": f"{self.prompt} and are having a conversation with someone, context:{input_message}"}]
        )
        return response["message"]["content"]
