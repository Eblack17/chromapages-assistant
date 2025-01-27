from langchain_community.chat_models import ChatGoogleGenerativeAI
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.schema import SystemMessage
import google.generativeai as genai
from config import *

def setup_gemini():
    """Initialize and configure Gemini model"""
    # Configure Google Gemini
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Initialize the Gemini model with configurations
    llm = ChatGoogleGenerativeAI(
        model=DEFAULT_MODEL,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        top_k=TOP_K,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        convert_system_message_to_human=True,
        verbose=VERBOSE
    )
    return llm

def create_conversation_memory():
    """Create conversation memory for the agents"""
    return ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

def initialize_chain(llm, memory):
    """Initialize the LangChain with system message"""
    system_message = SystemMessage(content="You are a helpful AI assistant.")
    
    chain = LLMChain(
        llm=llm,
        memory=memory,
        verbose=VERBOSE,
        prompt=MessagesPlaceholder(variable_name="chat_history")
    )
    return chain

def main():
    try:
        # Setup the environment
        llm = setup_gemini()
        memory = create_conversation_memory()
        chain = initialize_chain(llm, memory)
        
        print("Environment setup completed. Ready for agent implementation.")
    except Exception as e:
        print(f"Error during setup: {str(e)}")

if __name__ == "__main__":
    main() 
