from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def rewrite_query(question: str, history: list) -> str:
    """
    Rewrite the user's question into a standalone question using
    the conversation history.
    """

    conversation = "\n".join(
        f"{msg['role']}: {msg['content']}"
        for msg in history
    )

    prompt = f"""
You are a query rewriting assistant.

Your job is to rewrite the user's latest question into a
complete, standalone question.

Rules:
- Preserve the original meaning.
- Replace pronouns like "it", "they", "this", "that" with the correct entity.
- Do not answer the question.
- Return ONLY the rewritten question.

Conversation:
{conversation}

Latest Question:
{question}

Standalone Question:
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()