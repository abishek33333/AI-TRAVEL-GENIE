# import os
# from dotenv import load_dotenv
# from langchain_groq import ChatGroq
# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic

# load_dotenv()

# class ModelLoader:
#     """Load LLM with anti-hallucination settings"""
    
#     def __init__(self, model_provider="groq"):
#         self.model_provider = model_provider.lower()
        
#     def load_llm(self):
#         """Load LLM with settings optimized for factual accuracy"""
        
#         if self.model_provider == "groq":
#             api_key = os.getenv("GROQ_API_KEY")
#             if not api_key:
#                 raise ValueError("GROQ_API_KEY not found in environment")
            
#             print(f"🔧 Loading Groq LLM with anti-hallucination settings...")
            
#             # ✅ FIX: Use llama-3.3-70b which has 128K context window
#             # This model can handle much larger inputs than 8b-instant
#             return ChatGroq(
#                 model="meta-llama/llama-4-scout-17b-16e-instruct",  # Changed from llama-4-scout-17b
#                 temperature=0.1,  # VERY LOW to reduce hallucinations
#                 max_tokens=8000,
#                 api_key=api_key,
#                 model_kwargs={
#                     "top_p": 0.85,  # Reduced for more focused responses
#                     "frequency_penalty": 0.0,
#                     "presence_penalty": 0.0
#                 }
#             )
            
#         elif self.model_provider == "openai":
#             api_key = os.getenv("OPENAI_API_KEY")
#             if not api_key:
#                 raise ValueError("OPENAI_API_KEY not found")
            
#             print(f"🔧 Loading OpenAI GPT-4...")
#             return ChatOpenAI(
#                 model="gpt-4o",
#                 temperature=0.1,
#                 max_tokens=4000,
#                 api_key=api_key
#             )
            
#         elif self.model_provider == "anthropic":
#             api_key = os.getenv("ANTHROPIC_API_KEY")
#             if not api_key:
#                 raise ValueError("ANTHROPIC_API_KEY not found")
            
#             print(f"🔧 Loading Claude...")
#             return ChatAnthropic(
#                 model="claude-3-5-sonnet-20241022",
#                 temperature=0.1,
#                 max_tokens=4000,
#                 api_key=api_key
#             )
            
#         else:
#             raise ValueError(f"Unsupported model: {self.model_provider}")


import os
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

class ModelLoader:
    def __init__(self, model_provider: str = "openrouter"):
        self.model_provider = model_provider

    def load_llm(self) -> BaseChatModel:
        """
        Loads the LLM via OpenRouter's API with optimized settings.
        """
        if self.model_provider == "openrouter":
            # 1. Get API Key
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("❌ OPENROUTER_API_KEY is missing from environment variables.")

            # 2. Configure ChatOpenAI for OpenRouter with optimized settings
            return ChatOpenAI(
                # Use a more reliable model with better output
                # model="nvidia/nemotron-3-nano-30b-a3b:free",
                # Alternative models if above fails:
                # model="qwen/qwen3-next-80b-a3b-instruct:free",
                model="openai/gpt-oss-120b",
                
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                
                # Optimized temperature for consistent output
                temperature=0.3,  # Lower for more consistent output
                
                # Token limits - critical for free models
                max_tokens=8000,  # Increased to ensure complete responses
                
                # Timeout settings
                request_timeout=120,  # 2 minutes timeout
                
                # Required headers
                default_headers={
                    "HTTP-Referer": "http://localhost:8501",
                    "X-Title": "AI Travel Planner",
                },
                
                # Additional settings for reliability
                model_kwargs={
                    "top_p": 0.9,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                }
            )
        
        # Fallback for Gemini
        elif self.model_provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.3,
                max_output_tokens=4000,
            )
            
        else:
            raise ValueError(f"Unknown model provider: {self.model_provider}")