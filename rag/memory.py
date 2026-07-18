class ConversationMemory:
    def __init__(self, max_messages=6):
        self.messages = []
        self.max_messages = max_messages

    def add(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content
        })

        self.messages = self.messages[-self.max_messages:]

    def get_messages(self):
        return self.messages

    def clear(self):
        self.messages.clear()