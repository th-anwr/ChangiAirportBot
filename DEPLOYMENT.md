# Changi Airport Chatbot - Streamlit Deployment Guide

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file in your project root:
```
HF_TOKEN=your_huggingface_token_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

### 3. Get API Keys
- **HuggingFace Token**: Get from https://huggingface.co/settings/tokens
- **Pinecone API Key**: Get from https://app.pinecone.io/

### 4. Run Locally
```bash
streamlit run app/chatbot.py
```

## Deploy to Streamlit Cloud (FREE!)

### 1. Push to GitHub
Make sure your code is in a GitHub repository.

### 2. Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set the path to: `app/chatbot.py`
6. Add your environment variables (HF_TOKEN, PINECONE_API_KEY)
7. Deploy!

### 3. Share Your Link
Streamlit Cloud will give you a public URL like:
`https://your-app-name.streamlit.app`

## Features
- ✅ Free hosting on Streamlit Cloud
- ✅ No need for Ollama or local LLM
- ✅ Built-in chat interface
- ✅ Vector search with Pinecone
- ✅ HuggingFace Router for LLM access

## Troubleshooting
- Make sure your `.env` file is in the project root
- Check that your API keys are valid
- Ensure `data/source_data.txt` exists 