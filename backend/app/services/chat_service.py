from app.llm.chat_engine import chat_engine


class ChatService:

    def ask(self, question: str):

        return chat_engine.ask(question)


chat_service = ChatService()