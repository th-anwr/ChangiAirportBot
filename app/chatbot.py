import os
import asyncio
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
import nest_asyncio
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain import hub
import re

# Global variable to hold the final chatbot chain
final_agent_executor = None

class CustomAgentExecutor(AgentExecutor):
    """Custom AgentExecutor with better loop control and stopping conditions"""
    def __init__(self, *args, **kwargs):
        kwargs['max_iterations'] = kwargs.get('max_iterations', 5)
        kwargs['early_stopping_method'] = 'force'
        super().__init__(*args, **kwargs)

    def _should_continue(self, iterations: int, time_elapsed: float) -> bool:
        return iterations < self.max_iterations

def setup_and_build_advanced_chatbot(
    source_data_path: str = "data/source_data.txt",
    ollama_base_url: str = "http://localhost:11434",
    ollama_model: str = "llama3"
):
    global final_agent_executor

    # --- Part A: Setup LLM ---
    print("--- Step 1: Setting up LLM ---")
    nest_asyncio.apply()
    llm = Ollama(base_url=ollama_base_url, model=ollama_model)

    # --- Part B: Load Data ---
    print(f"--- Step 2: Loading data from {source_data_path} ---")
    if not os.path.exists(source_data_path):
        raise FileNotFoundError(f"Source data file not found: {source_data_path}")
    with open(source_data_path, "r", encoding="utf-8") as f:
        text = f.read()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_text(text)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    # --- Part C: Tools ---
    def enhanced_retriever(query: str) -> str:
        try:
            retriever_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            result = retriever_chain.invoke({"query": query})
            answer = result.get('result', '').strip()
            no_answer_indicators = [
                "i don't know", "no information", "don't have",
                "cannot provide", "not mentioned", "no specific",
                "recommend searching elsewhere", "contact the airport directly"
            ]
            if any(indicator in answer.lower() for indicator in no_answer_indicators):
                return "NO_RELEVANT_INFO_FOUND"
            if any(keyword in query.lower() for keyword in ['restaurant', 'food', 'dining', 'eat']):
                answer += "\n\nFor directions to restaurants, check the airport directory screens or ask airport staff. Most restaurants display their operating hours and some offer online reservations."
            elif any(keyword in query.lower() for keyword in ['hotel', 'accommodation', 'stay']):
                answer += "\n\nFor hotel bookings and exact directions, you can visit the hotel's reception desk or check the airport's interactive maps. Many airport hotels offer shuttle services."
            elif any(keyword in query.lower() for keyword in ['transport', 'bus', 'taxi', 'mrt', 'train']):
                answer += "\n\nFor current transport schedules and costs, check the official transport counters at the airport. Prices may vary based on destination and time of day."
            elif any(keyword in query.lower() for keyword in ['shop', 'shopping', 'store', 'buy']):
                answer += "\n\nFor store locations, check the airport directory or ask at information counters. Store hours may vary, and some shops offer tax-free shopping for international travelers."
            return answer
        except Exception as e:
            return f"Error accessing airport knowledge base: {str(e)}"

    def real_time_status(query: str) -> str:
        if "flight status" in query.lower() or re.search(r'[A-Z]{2}\d+', query, re.IGNORECASE):
            return ("For the most accurate and real-time flight status, please check the official "
                    "Singapore Changi Airport website (https://www.changiairport.com/en/flight/departures.html) "
                    "or the airline's official mobile application.")
        else:
            return "Final Answer: Please try rephrasing your question."

    tools = [
        Tool(
            name="Airport_Knowledge_Base",
            func=enhanced_retriever,
            description="Primary tool for questions about airport facilities, services, shops, restaurants, hotels, transport, and policies. Always use this first for airport-related questions."
        ),
        Tool(
            name="Real_Time_Flight_Status",
            func=real_time_status,
            description="Use for real-time information like flight status, weather, current prices, or when the knowledge base doesn't have the answer."
        )
    ]

    prompt = hub.pull("hwchase17/react-chat")
    prompt.template = """
    You are a helpful assistant for Changi Airport (including all terminals T1, T2, T3, T4) and Jewel Changi Airport.
    Your goal is to provide comprehensive and accurate information about both locations.

    IMPORTANT CONTEXT RULES:
    1. **Multi-Airport Context**: When users ask about restaurants, hotels, shops, or services without specifying a location,
       automatically provide information from BOTH Changi Airport terminals AND Jewel Changi Airport.
    2. **Enhanced Information**: For restaurants, hotels, transport, and services, always try to include:
       - Location/directions when possible
       - add map link as reference "https://www.changiairport.com/en/at-changi/map.html"
       - Operating hours if available
       - Approximate costs or price ranges if mentioned
       - Contact information if available

    TOOL USAGE STRATEGY - FOLLOW THIS EXACTLY:
    1. **Step 1**: ALWAYS try `Airport_Knowledge_Base` first for airport-related questions
    2. **Step 2**: If `Airport_Knowledge_Base` returns "NO_RELEVANT_INFO_FOUND", then use `Real_Time_Flight_Status`
    3. **Step 3**: Once you get useful information from ANY tool, provide your final answer immediately

    CRITICAL RULES:
    - NEVER use the same tool twice in one conversation
    - If Airport_Knowledge_Base gives useful info → Provide final answer immediately
    - If Airport_Knowledge_Base says "NO_RELEVANT_INFO_FOUND" → Use Real_Time_Flight_Status once, then final answer
    - If both tools fail → Acknowledge limitation and provide final answer

    TOOLS:
    ------
    You have access to the following tools: {tools}

    RESPONSE FORMAT:
    Use this exact format:

    ```
    Thought: [Your reasoning about what the user is asking and which tool to use]
    Action:
    ```
    {{
      "action": "[tool name]",
      "action_input": "[search query]"
    }}
    ```
    Observation: [tool result]
    ```

    When you have information to answer, IMMEDIATELY use:
    ```
    Thought: I now have information to answer the user's question.
    Final Answer: [Your detailed, helpful answer with locations, directions, and additional context]
    ```

    IMPORTANT: Your final answer MUST always start with "Final Answer:" and be in the format:
    Thought: I now have information to answer the user's question.
    Final Answer: [your answer here]
    If you don't know, say: "Final Answer: Please try rephrasing your question."
    NEVER output anything outside this format.

    REMEMBER:
    - Always consider both Changi Airport terminals and Jewel when location isn't specified
    - Include practical details like directions and costs when available
    - Provide final answer as soon as you have useful information

    Question: {input}
    {agent_scratchpad}
    """

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = CustomAgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=3,
        early_stopping_method='force',
        handle_parsing_errors="Check your output and make sure it conforms to the format instructions."
    )

    expansion_prompt_template = """
    You are a query enhancement assistant for Changi Airport and Jewel. Your task is to improve user questions by:
    1. Adding airport context when missing
    2. Making questions more specific for better search results
    3. Ensuring multi-location queries are comprehensive

    Enhancement Rules:
    - For general questions about restaurants/food: Add "at Changi Airport terminals and Jewel"
    - For general questions about hotels: Add "at or near Changi Airport and Jewel"
    - For general questions about shops/shopping: Add "at Changi Airport and Jewel"
    - For transport questions: Add "from/to Changi Airport"
    - For specific named places: Keep as is but ensure clarity

    Examples:
    User: "can you suggest some restaurants"
    Enhanced: "can you suggest restaurants at Changi Airport terminals and Jewel with their locations and operating hours"

    User: "where is YOTELAIR hotel"
    Enhanced: "where is YOTELAIR hotel at Changi Airport with directions and contact information"

    User: "how to get to city center"
    Enhanced: "how to get from Changi Airport to city center with transport options and costs"

    User question: {question}
    Enhanced question:
    """

    EXPANSION_PROMPT = PromptTemplate(template=expansion_prompt_template, input_variables=["question"])
    query_expansion_chain = EXPANSION_PROMPT | llm | StrOutputParser()

    def safe_agent_invoke(inputs: str) -> str:
        try:
            result = agent_executor.invoke({"input": inputs})
            if isinstance(result, dict) and 'output' in result:
                output = result['output']
            else:
                output = str(result)
            if not output.strip().lower().startswith("final answer:"):
                output = f"Final Answer: {output.strip()}"
            return output
        except Exception as e:
            return "Final Answer: Please try rephrasing your question."

    final_chain = RunnableLambda(lambda x: query_expansion_chain.invoke({"question": x["question"]})) | RunnableLambda(safe_agent_invoke)
    final_agent_executor = final_chain
    print("Chatbot is ready.")

# Helper function for testing
def test_chatbot(question: str):
    if final_agent_executor is None:
        return "Chatbot not initialized. Please run setup first."
    try:
        response = final_agent_executor.invoke({"question": question})
        return response
    except Exception as e:
        return f"Error: {str(e)}"

# CLI main function
def main():
    setup_and_build_advanced_chatbot()
    print("\n--- Changi Airport AI Agent (CLI Interface) ---")
    print("The agent will show its 'thought process' before giving a final answer.")
    print("Type 'exit' to end the conversation.")
    while True:
        query = input("\nYour question: ")
        if query.lower() == 'exit':
            print("Chat session ended.")
            break
        try:
            result = final_agent_executor.invoke({"question": query})
            print("\nFinal Answer:", result)
        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()