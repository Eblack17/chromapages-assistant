from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.text_splitter import MarkdownTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import google.generativeai as genai
from config import *
import markdown
import os

class ChromapagesRAGAgent:
    def __init__(self):
        self.llm = self._setup_llm()
        self.embeddings = self._setup_embeddings()
        self.vector_store = self._setup_vector_store()
        self.chain = self._setup_chain()

    def _setup_llm(self):
        """Initialize and configure Gemini model"""
        genai.configure(api_key=GOOGLE_API_KEY)
        return ChatGoogleGenerativeAI(
            model=DEFAULT_MODEL,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            top_k=TOP_K,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            convert_system_message_to_human=True,
            verbose=VERBOSE
        )

    def _setup_embeddings(self):
        """Setup Google Generative AI embeddings"""
        return GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    def _setup_vector_store(self):
        """Setup Chroma vector store with knowledge base"""
        # Read and split the knowledge base
        with open("knowledgebase.md", "r", encoding="utf-8") as f:
            knowledge_base = f.read()

        text_splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = text_splitter.split_text(knowledge_base)

        # Create or load vector store
        if os.path.exists("chroma_db"):
            return Chroma(persist_directory="chroma_db", embedding_function=self.embeddings)
        else:
            return Chroma.from_texts(
                texts,
                self.embeddings,
                persist_directory="chroma_db"
            )

    def _setup_chain(self):
        """Setup the retrieval QA chain"""
        # Create a custom prompt template
        template = """You are a knowledgeable customer service representative for Chromapages, 
        a web design and development company. Use the following context to answer questions accurately 
        and professionally. If you don't find the specific information in the context, say so politely 
        and offer to help with related information you do have.

        Context: {context}
        
        Question: {question}
        
        Answer the question based on the context provided."""

        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            ),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True,
            verbose=VERBOSE
        )

    def chat(self, question: str) -> str:
        """Process a question and return the response"""
        try:
            result = self.chain.invoke({"query": question})
            return result["result"]
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"

def main():
    # Initialize the RAG agent
    agent = ChromapagesRAGAgent()
    
    print("Chromapages Assistant: Hello! I'm here to help you with questions about Chromapages' services. What would you like to know?")
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Chromapages Assistant: Goodbye! Have a great day!")
            break
            
        response = agent.chat(user_input)
        print(f"Chromapages Assistant: {response}")

if __name__ == "__main__":
    main() 
