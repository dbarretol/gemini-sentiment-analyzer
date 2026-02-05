import os
import json
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import types


ALLOWED = {"positivo", "negativo", "neutro"}


# JSON schema (formato "OBJECT" / "ARRAY" que usa el SDK)
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "required": ["results"],
    "properties": {
        "results": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "required": ["id", "label"],
                "properties": {
                    "id": {"type": "INTEGER"},
                    "label": {"type": "STRING"}  # positivo|negativo|neutro
                },
            },
        }
    },
}


def load_comments(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("comments", [])


def chunk_list(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def normalize_results(results: List[Dict[str, Any]], ids_expected: List[int]) -> List[Dict[str, Any]]:
    """Asegura que haya un resultado por id y que label sea válido."""
    by_id = {}
    for r in results or []:
        try:
            rid = int(r.get("id"))
        except Exception:
            continue
        label = str(r.get("label", "")).lower().strip()
        if label not in ALLOWED:
            label = "neutro"
        by_id[rid] = {"id": rid, "label": label}

    # Completa faltantes como neutro
    out = []
    for cid in ids_expected:
        out.append(by_id.get(cid, {"id": cid, "label": "neutro"}))
    return out


def classify_batch(client: genai.Client, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ids = [int(c["id"]) for c in comments]

    # Mandamos los comentarios como JSON al modelo para minimizar ambigüedad
    payload = [{"id": int(c["id"]), "text": str(c["text"])} for c in comments]

    prompt = (
        "Clasifica el sentimiento de cada comentario de redes sociales en español.\n"
        "Etiquetas permitidas: positivo, negativo, neutro.\n"
        "Devuelve un JSON con la misma cantidad de elementos que entradas.\n"
        "No inventes ids; usa exactamente los ids dados.\n"
    )

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            "ENTRADAS (JSON):",
            json.dumps(payload, ensure_ascii=False),
        ],
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
        ),
    )

    # Con response_schema normalmente viene parseado:
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, dict) and "results" in parsed:
        return normalize_results(parsed.get("results", []), ids)

    # Fallback si por alguna razón no viene parsed
    try:
        raw = (resp.text or "").strip()
        data = json.loads(raw)
        return normalize_results(data.get("results", []), ids)
    except Exception:
        return [{"id": cid, "label": "neutro"} for cid in ids]


def main():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en el .env (o GOOGLE_API_KEY).")

    client = genai.Client(api_key=api_key)

    comments = load_comments("comments.json")
    if not comments:
        raise RuntimeError("No hay comentarios en comments.json")

    # 1 llamada si son pocos.
    # Si en el futuro metes cientos/miles, esto evita sobrepasar tokens.
    CHUNK_SIZE = 50  # para tus 30, será 1 sola llamada

    all_results: List[Dict[str, Any]] = []
    for part in chunk_list(comments, CHUNK_SIZE):
        part_results = classify_batch(client, part)
        all_results.extend(part_results)

    # Unimos label con texto original para imprimir y guardar
    by_id = {r["id"]: r["label"] for r in all_results}
    merged = []
    for c in comments:
        cid = int(c["id"])
        merged.append(
            {"id": cid, "text": c["text"], "label": by_id.get(cid, "neutro")}
        )

    # imprime
    for r in merged:
        print(f'[{r["id"]}] {r["label"]} - {r["text"]}')

    # guarda
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump({"results": merged}, f, ensure_ascii=False, indent=2)

    client.close()


if __name__ == "__main__":
    main()