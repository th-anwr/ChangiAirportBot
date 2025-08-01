import streamlit as st
import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

def setup_chatbot():
    """Setup the chatbot components"""
    
    # Get environment variables
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    HF_TOKEN = os.environ.get("HF_TOKEN")
    index_name = "jewel-changi-airport-index"
    
    if not PINECONE_API_KEY or not HF_TOKEN:
        return None
    
    # Load documents
    DATA_PATH = "../data/source_data.txt"
    
    def load_txt_file(file_path):
        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
        return documents
    
    try:
        documents = load_txt_file(DATA_PATH)
    except Exception as e:
        return None
    
    # Create chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    text_chunks = text_splitter.split_documents(documents)
    
    # Initialize embedding model
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Setup Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Check if index exists, if not create it
    if index_name not in [index.name for index in pc.list_indexes()]:
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        import time
        time.sleep(10)
    
    # Create or connect to vector store
    try:
        docsearch = PineconeVectorStore.from_existing_index(
            index_name=index_name,
            embedding=embedding_model
        )
    except Exception as e:
        docsearch = PineconeVectorStore.from_texts(
            texts=[chunk.page_content for chunk in text_chunks],
            embedding=embedding_model,
            index_name=index_name
        )
    
    retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    
    # Initialize LLM
    llm = ChatOpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=HF_TOKEN,
        model="Qwen/Qwen3-Coder-480B-A35B-Instruct:novita",
        temperature=0.2,
        max_tokens=512
    )
    
    # Create prompt template
    CUSTOM_PROMPT_TEMPLATE = """
    You are a helpful assistant for Changi Airport (Terminals T1, T2, T3, T4) and Jewel Changi Airport.
    Provide concise, direct answers about airport facilities, services, shops, restaurants, hotels, and transport.
    Try to use sentence in place of headers and subheaders.
    
    Guidelines:
    - Give brief, practical information 
    - Include location and operating hours when relevant
    - Mention costs and contacts if available
    - For general questions, cover both airport terminals and Jewel
    - Include map link: https://www.changiairport.com/en/at-changi/map.html
    
    Context: {context}
    Question: {question}
    
    Answer:
    """
    
    prompt = PromptTemplate(template=CUSTOM_PROMPT_TEMPLATE, input_variables=["context", "question"])
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={'prompt': prompt}
    )
    
    return qa_chain

def main():
    st.write("Changi Airport Chatbot")    
    # Initialize chatbot
    if 'qa_chain' not in st.session_state:
        with st.spinner("Setting up chatbot..."):
            st.session_state.qa_chain = setup_chatbot()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input - always show this
    user_input = st.chat_input("Ask your question about Changi Airport...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get chatbot response
        with st.chat_message("assistant"):
            if st.session_state.qa_chain is None:
                st.error("Chatbot not ready. Please check your environment variables.")
            else:
                with st.spinner("Thinking..."):
                    try:
                        response = st.session_state.qa_chain.invoke({'query': user_input})
                        answer = response["result"]
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        st.markdown("Please rephrase your question.")
    
    # Show status if chatbot is not ready
    if st.session_state.qa_chain is None:
        st.warning(" Chatbot is still setting up. Please wait...")

if __name__ == "__main__":
    main() 