# Changi Airport Chatbot (Streamlit + Pinecone + HuggingFace)

A Retrieval-Augmented Generation (RAG) chatbot for Changi Airport and Jewel, powered by HuggingFace embeddings, Pinecone vector database, and Qwen LLM. Features a clean Streamlit web interface for easy interaction.

---

## Features

- **Local Knowledge Base:** Uses your own `source_data.txt` for airport info.
- **LLM-Powered:** Uses Qwen model via HuggingFace Router for natural language answers.
- **Pinecone Vector Database:** Cloud-based vector storage for efficient similarity search.
- **Streamlit Web Interface:** Clean, user-friendly chat interface.
- **Concise Responses:** Direct, practical answers without verbose formatting.
- **No External Web Search:** All answers are from your local data.

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

### 3. Set Environment Variables

You'll need to set up the following environment variables:

```bash
# For Pinecone vector database
export PINECONE_API_KEY=your-pinecone-api-key

# For HuggingFace Router
export HF_TOKEN=your-huggingface-token
```

Or create a `.env` file in the project root:

```bash
PINECONE_API_KEY=your-pinecone-api-key
HF_TOKEN=your-huggingface-token
```

---

## Running the Chatbot

Start the Streamlit application:

```bash
cd app
streamlit run chatbot.py
```

The chatbot will automatically:
1. Load your source data
2. Create embeddings using HuggingFace
3. Set up Pinecone vector database
4. Initialize the Qwen LLM
5. Launch the web interface

---

## Usage

1. **Open your browser** to the URL shown in the terminal (usually `http://localhost:8501`)
2. **Wait for setup** - the chatbot will initialize automatically
3. **Start chatting** - ask questions about Changi Airport and Jewel
4. **Get concise answers** - responses are direct and practical

---

## Project Structure

```
app/
  chatbot.py      # Main Streamlit chatbot application
  main.py         # FastAPI app (legacy, not used in current version)
data/
  source_data.txt # Your knowledge base
requirements.txt
README.md
```

---

## Features

- **Automatic Setup:** No manual configuration needed
- **Chat History:** Maintains conversation during session
- **Error Handling:** Graceful error messages
- **Responsive Design:** Works on desktop and mobile
- **Real-time Processing:** Immediate responses

---

## Security

- Keep your Pinecone API key secure
- Keep your HuggingFace token secure
- No sensitive data is stored locally

---

## Troubleshooting

- **Environment Variables:** Ensure `PINECONE_API_KEY` and `HF_TOKEN` are set
- **Data File:** Make sure `data/source_data.txt` exists and is not empty
- **Pinecone Credits:** Ensure you have sufficient Pinecone credits
- **Internet Connection:** Required for HuggingFace and Pinecone services

---

## Example Questions

- "Where can I eat at Changi Airport?"
- "What shops are in Terminal 3?"
- "How do I get to Jewel from Terminal 1?"
- "What are the operating hours for restaurants?"
- "Where can I find luxury brands?" 