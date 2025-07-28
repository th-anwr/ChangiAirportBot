# Changi Airport Chatbot (FastAPI + Ollama + FAISS)

A Retrieval-Augmented Generation (RAG) chatbot for Changi Airport and Jewel, powered by local embeddings, FAISS, and an LLM served by Ollama. Exposes a secure FastAPI web API for easy integration and sharing.

---

## Features

- **Local Knowledge Base:** Uses your own `source_data.txt` for airport info.
- **LLM-Powered:** Uses Ollama (e.g., Llama3) for natural language answers.
- **FastAPI Web API:** Easily deployable and accessible via HTTP.
- **API Key Security:** Protects your endpoint with an API key.
- **No External Web Search:** All answers are from your local data or static flight status info.

---

## Setup

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd <your-repo>
pip install -r requirements.txt
```

### 2. Prepare Data

- Place your knowledge base text in `data/source_data.txt`.

### 3. Start Ollama

Make sure [Ollama](https://ollama.com/) is installed and running, and the model (e.g., `llama3`) is available:

```bash
ollama serve
ollama pull llama3
```

### 4. Set API Key (Optional but recommended)

Set an environment variable for your API key:

```bash
export CHATBOT_API_KEY=your-secret-api-key
```
Or edit the value in `app/main.py`.

---

## Running the API

Start the FastAPI server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## API Usage

### **POST /chat**

- **Request Body:**
  ```json
  {
    "question": "Where can I eat at Changi Airport?",
    "api_key": "your-secret-api-key"
  }
  ```
- **Response:**
  ```json
  {
    "answer": "Final Answer: [detailed answer here]"
  }
  ```

---

## Deployment

- For a public link, deploy to [Railway](https://railway.app/), [Render](https://render.com/), or similar.
- Or use [ngrok](https://ngrok.com/) for a quick public tunnel:
  ```bash
  ngrok http 8000
  ```
  Share the generated public URL.

---

## Project Structure

```
app/
  chatbot.py      # Main chatbot logic (LLM, retrieval, prompt, etc.)
  main.py         # FastAPI app exposing the /chat endpoint
data/
  source_data.txt # Your knowledge base
requirements.txt
README.md
```

---

## Security

- All API requests require the correct API key.
- Do not share your API key publicly.

---

## Example cURL Request

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Where can I eat at Changi Airport?", "api_key": "your-secret-api-key"}'
```

---

## Troubleshooting

- Ensure Ollama is running and the model is pulled.
- Ensure `data/source_data.txt` exists and is not empty.
- Check your API key matches the server’s. 