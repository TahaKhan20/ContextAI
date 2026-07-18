import re


def clean_text(text: str):

    text = re.sub(r"\n+", "\n", text)

    text = re.sub(r"\s+", " ", text)

    text = text.replace("Python Programming", "")

    return text.strip()