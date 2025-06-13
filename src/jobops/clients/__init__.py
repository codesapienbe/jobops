from abc import abstractmethod
import logging
from typing import Any, Dict, Optional

import ollama
from typing import Protocol

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from xgrok import XGrokClient  # Hypothetical SDK
except ImportError:
    XGrokClient = None

try:    
    from perplexity import Perplexity  # Hypothetical SDK
except ImportError:
    Perplexity = None

class BaseLLMBackend(Protocol):
    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str: pass
    @abstractmethod
    def health_check(self) -> bool: pass
    @abstractmethod
    def embed_structured_data(self, job_data) -> list: pass

def embed_structured_data(text: str) -> list:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(text).tolist()

class OllamaBackend(BaseLLMBackend):
    name = "ollama"
    def __init__(self, model: str = "llama3:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        ollama.base_url = base_url
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._logger.info(f"Generating response with model: {self.model}")
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = ollama.chat(model=self.model, messages=messages)
            return response['message']['content']
        except Exception as e:
            self._logger.error(f"Ollama generation error: {e}")
            raise
    
    def health_check(self) -> bool:
        try:
            return True
            # resp = requests.get("http://localhost:8000/health/ollama")
            # return resp.status_code == 200 and resp.json().get("status") == "ok"
        except Exception as e:
            self._logger.error(f"Proxy health check failed: {e}")
            return False

    def embed_structured_data(self, job_data):
        try:
            return embed_structured_data(job_data.description)
        except Exception as e:
            self._logger.error(f"Ollama embedding error: {e}")
            raise

class OpenAIBackend(BaseLLMBackend):
    name = "openai"
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1"):
        if not api_key:
            raise ValueError("OpenAI API key required")
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._logger.info(f"Generating response with model: {self.model}")
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=3000
            )
            return response.choices[0].message.content
        except Exception as e:
            self._logger.error(f"OpenAI generation error: {e}")
            raise
    
    def health_check(self) -> bool:
        try:
            return True
            # resp = requests.get("http://localhost:8000/health/openai")
            # return resp.status_code == 200 and resp.json().get("status") == "ok"
        except Exception as e:
            self._logger.error(f"Proxy health check failed: {e}")
            return False

    def embed_structured_data(self, job_data):
        try:
            return embed_structured_data(job_data.description)
        except Exception as e:
            self._logger.error(f"OpenAI embedding error: {e}")
            raise


class GroqBackend(BaseLLMBackend):
    name = "groq"
    def __init__(self, api_key: str, model: str = "mistral:7b-instruct-q4_0", base_url: str = "https://api.groq.com/openai/v1"):
        if not api_key:
            raise ValueError("Groq API key required")
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = model
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._logger.info(f"Generating response with model: {self.model}")
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=3000
            )
            return response.choices[0].message.content
        except Exception as e:
            self._logger.error(f"Groq generation error: {e}")
            raise
    
    def health_check(self) -> bool:
        try:
            return True
            # resp = requests.get("http://localhost:8000/health/groq")
            # return resp.status_code == 200 and resp.json().get("status") == "ok"
        except Exception as e:
            self._logger.error(f"Proxy health check failed: {e}")
            return False
        
    def embed_structured_data(self, job_data):
        try:
            return embed_structured_data(job_data.description)
        except Exception as e:
            self._logger.error(f"Groq embedding error: {e}")
            raise
            

class GoogleGeminiBackend(BaseLLMBackend):
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        if not api_key:
            raise ValueError("Gemini API key required")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self._logger = logging.getLogger(self.__class__.__name__)

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._logger.info(f"Generating response with model: {self.model}")
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            self._logger.error(f"Gemini generation error: {e}")
            raise

    def health_check(self) -> bool:
        try:
            return True
            # return genai.get_model(self.model.name) is not None
        except Exception as e:
            self._logger.error(f"Gemini health check failed: {e}")
            return False

    def embed_structured_data(self, job_data):
        try:
            return embed_structured_data(job_data.description)
        except Exception as e:
            self._logger.error(f"Gemini embedding error: {e}")
            raise

class XGrokBackend(BaseLLMBackend):
    def __init__(self, api_key: str, model: str = "grok-1"):
        if not api_key:
            raise ValueError("X Grok API key required")
        self.client = XGrokClient(api_key=api_key)
        self.model = model
        self._logger = logging.getLogger(self.__class__.__name__)

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._logger.info(f"Generating response with model: {self.model}")
        try:
            messages = [{"role": "user", "content": prompt}]
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=3000
            )
            return response.choices[0].message.content
        except Exception as e:
            self._logger.error(f"X Grok generation error: {e}")
            raise

    def health_check(self) -> bool:
        try:
            return True
            # return self.client.ping()
        except Exception as e:
            self._logger.error(f"X Grok health check failed: {e}")
            return False

    def embed_structured_data(self, job_data):
        try:
            return embed_structured_data(job_data.description)
        except Exception as e:
            self._logger.error(f"X Grok embedding error: {e}")
            raise

class PerplexityBackend(BaseLLMBackend):
    def __init__(self, api_key: str, model: str = "pplx-7b-online"):
        if not api_key:
            raise ValueError("Perplexity API key required")
        self.client = Perplexity(api_key=api_key)
        self.model = model
        self._logger = logging.getLogger(self.__class__.__name__)

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._logger.info(f"Generating response with model: {self.model}")
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=3000
            )
            return response.choices[0].message.content
        except Exception as e:
            self._logger.error(f"Perplexity generation error: {e}")
            raise

    def health_check(self) -> bool:
        try:
            return True
            # return self.client.models.list() is not None
        except Exception as e:
            self._logger.error(f"Perplexity health check failed: {e}")
            return False

    def embed_structured_data(self, job_data):
        try:
            return embed_structured_data(job_data.description)
        except Exception as e:
            self._logger.error(f"Perplexity embedding error: {e}")
            raise

class LLMBackendFactory:
    @staticmethod
    def create(backend_type: str, settings: Dict[str, Any], tokens: Dict[str, str]) -> BaseLLMBackend:
        ollama_model = settings.get('model', 'qwen3:1.7b')
        groq_model = settings.get('model', 'llama-3.3-70b-versatile')
        openai_model = settings.get('model', 'gpt-4o-mini')
        gemini_model = settings.get('model', 'gemini-1.5-pro')
        perplexity_model = settings.get('model', 'pplx-7b-online')
        xgrok_model = settings.get('model', 'grok-1')
        
        if backend_type == "ollama":
            return OllamaBackend(
                model=ollama_model,
                base_url=settings.get('base_url', 'http://localhost:11434')
            )
        elif backend_type == "openai":
            return OpenAIBackend(
                api_key=tokens.get('openai', ''),
                model=openai_model
            )
        elif backend_type == "groq":
            return GroqBackend(
                api_key=tokens.get('groq', ''),
                model=groq_model
            )
        elif backend_type == "gemini":
            return GoogleGeminiBackend(
                api_key=tokens.get('gemini', ''),
                model=gemini_model
            )
        elif backend_type == "xgrok":
            return XGrokBackend(
                api_key=tokens.get('xgrok', ''),
                model=xgrok_model
            )
        elif backend_type == "perplexity":
            return PerplexityBackend(
                api_key=tokens.get('perplexity', ''),
                model=perplexity_model
            )
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")