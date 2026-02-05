# Sentiment Analysis (Positivo / Negativo / Neutro) con Gemini (Google Gen AI SDK)

Este proyecto clasifica comentarios de redes sociales en **positivo**, **negativo** o **neutro** usando **Gemini** a través del SDK oficial **`google-genai`**.

A diferencia de una implementación “uno por uno”, este script envía **todos los comentarios en una sola llamada** (o en bloques si aumentas la cantidad), evitando llegar al límite de llamadas de la API y reduciendo errores por rate limit.

---

## Requisitos

- Python 3.10+ (recomendado 3.11/3.12)
- [`uv`](https://github.com/astral-sh/uv) instalado
- Una API Key de Gemini Developer API

---

## Estructura del proyecto

Ejemplo:

```
DSRP-SENTIMENT-ANALYSIS/
  .env
  comments.json
  analyze_sentiment_batch.py
  results.json   (se genera al ejecutar)
```

---

## 1) Instalación de dependencias

En la carpeta del proyecto:

```bash
uv add google-genai python-dotenv
```

> Esto crea/usa un entorno virtual y gestiona las dependencias automáticamente.

---

## 2) Configurar la API Key

Crea un archivo **`.env`** en la raíz del proyecto con:

```env
GEMINI_API_KEY=TU_API_KEY_AQUI
```

Notas:
- Recomendado **sin comillas**.
- No compartas tu API key. Agrega `.env` a tu `.gitignore`.

---

## 3) Crear comentarios de prueba (`comments.json`)

Crea un archivo **`comments.json`** con este formato:

```json
{
  "comments": [
    { "id": 1, "text": "Me encantó el producto, llegó rapidísimo." },
    { "id": 2, "text": "Pésimo servicio, nadie responde y perdí mi dinero." },
    { "id": 3, "text": "Ok, gracias por la info." }
  ]
}
```

Reglas:
- `id` debe ser un número (entero).
- `text` es el comentario a evaluar.

---

## 4) Ejecutar el análisis

Ejecuta:

```bash
uv run python analyze_sentiment_batch.py
```

Verás resultados en consola, por ejemplo:

```
[1] positivo - Me encantó el producto, llegó rapidísimo.
[2] negativo - Pésimo servicio, nadie responde y perdí mi dinero.
[3] neutro - Ok, gracias por la info.
```

Y se generará un archivo **`results.json`**.

---

## 5) Salida (`results.json`)

El script genera un JSON con el sentimiento por comentario:

```json
{
  "results": [
    { "id": 1, "text": "Me encantó el producto, llegó rapidísimo.", "label": "positivo" },
    { "id": 2, "text": "Pésimo servicio, nadie responde y perdí mi dinero.", "label": "negativo" },
    { "id": 3, "text": "Ok, gracias por la info.", "label": "neutro" }
  ]
}
```

---

## Cómo funciona (resumen)

- Lee la API key desde `.env` usando `python-dotenv`
- Lee comentarios desde `comments.json`
- Envía la lista de comentarios a Gemini en **una sola llamada**
- Gemini devuelve un JSON estructurado con `{id, label}`
- El script valida etiquetas permitidas: `positivo`, `negativo`, `neutro`
- Guarda el resultado en `results.json`

---

## Configuración opcional: tamaño de bloque (chunk)

Dentro de `analyze_sentiment_batch.py` existe:

```python
CHUNK_SIZE = 50
```

- Con 30 comentarios, se hace **1 llamada**
- Si subes a cientos/miles, el script divide en bloques para no exceder tokens

Puedes ajustar ese valor según tu caso.

---

## Solución de problemas

### `Missing GEMINI_API_KEY...`
- Revisa que `.env` exista en la raíz del proyecto
- Asegúrate de que contenga `GEMINI_API_KEY=...`
- Evita comillas en el valor

### `503 UNAVAILABLE`
Es un error temporal del servicio. Reintenta.
Si necesitas más robustez, se puede agregar “retry con backoff” (reintentos automáticos).

### Resultados “raros”
El modelo es probabilístico. Para reducir variación el script usa `temperature=0`.
Si aun así quieres más consistencia, se puede mejorar el prompt o usar un schema más estricto.

---

## Licencia
Uso libre para fines educativos/prototipos. Ajusta según tu proyecto.