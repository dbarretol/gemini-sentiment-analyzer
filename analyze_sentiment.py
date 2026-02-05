import os
import json
from enum import Enum
from typing import List, Dict, Any

from dotenv import load_dotenv
from google import genai
from google.genai import types


class SentimentEnum(str, Enum):
    positivo = "positivo"
    negativo = "negativo"
    neutro = "neutro"


def load_comments(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("comments", [])


def classify_comment(client: genai.Client, text: str) -> str:
    prompt = (
        "Clasifica el siguiente comentario de redes sociales en español "
        "como positivo, negativo o neutro.\n\n"
        f"Comentario: {text}"
    )

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="text/x.enum",
            response_schema=SentimentEnum,  # fuerza una de las 3 etiquetas
        ),
    )

    label = (resp.text or "").strip().lower()
    if label not in {s.value for s in SentimentEnum}:
        # fallback defensivo (raro con enum)
        return "neutro"
    return label


def main():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en tu .env (o GOOGLE_API_KEY).")

    client = genai.Client(api_key=api_key)

    comments = load_comments("comments.json")
    results = []

    for c in comments:
        cid = c.get("id")
        text = c.get("text", "")
        label = classify_comment(client, text)

        results.append({"id": cid, "text": text, "label": label})
        print(f"[{cid}] {label} - {text}")

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, ensure_ascii=False, indent=2)

    client.close()


if __name__ == "__main__":
    main()