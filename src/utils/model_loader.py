import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv()

class ModelLoader:
    """Load LLM with anti-hallucination settings"""
    
    def __init__(self, model_provider="groq"):
        self.model_provider = model_provider.lower()
        
    def load_llm(self):
        """Load LLM with settings optimized for factual accuracy"""
        
        if self.model_provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            
            print(f"🔧 Loading Groq LLM with anti-hallucination settings...")
            
            # ✅ FIX: Use llama-3.3-70b which has 128K context window
            # This model can handle much larger inputs than 8b-instant
            return ChatGroq(
                model="meta-llama/llama-4-scout-17b-16e-instruct",  # Changed from llama-4-scout-17b
                temperature=0.1,  # VERY LOW to reduce hallucinations
                max_tokens=8000,
                api_key=api_key,
                model_kwargs={
                    "top_p": 0.85,  # Reduced for more focused responses
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0
                }
            )
            
        elif self.model_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found")
            
            print(f"🔧 Loading OpenAI GPT-4...")
            return ChatOpenAI(
                model="gpt-4o",
                temperature=0.1,
                max_tokens=4000,
                api_key=api_key
            )
            
        elif self.model_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found")
            
            print(f"🔧 Loading Claude...")
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                temperature=0.1,
                max_tokens=4000,
                api_key=api_key
            )
            
        else:
            raise ValueError(f"Unsupported model: {self.model_provider}")