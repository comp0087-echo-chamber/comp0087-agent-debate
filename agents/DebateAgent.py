import ollama

class DebateAgent:
    def __init__(self, name, model, prompt):
        self.name = name
        self.model = model
        self.prompt = prompt

    def respond(self, conversation_history):
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": f"{self.prompt}. Keep your response within 50 words. Conversation history: {conversation_history}"}]
        )
        return response["message"]["content"]
