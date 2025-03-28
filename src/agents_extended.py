import os
import subprocess
from .agents import GameMasterAgent
import ollama
from google import genai

class DeepSeekAgent(GameMasterAgent):
    """
    A GameMasterAgent implementation that uses the DeepSeek model via Ollama.
    This class is designed to work in Google Colab environments.
    """
    
    def __init__(self, deep_research: bool = False, max_iterations: int = 3):
        """
        Initialize the DeepSeekAgent and set up the Ollama environment.
        
        Args:
            deep_research (bool): Whether to use iterative refinement for responses
            max_iterations (int): Maximum number of refinement iterations
        """
        super().__init__(deep_research=deep_research, max_iterations=max_iterations)
        self.model = "deepseek-r1:7b"
        self._setup_ollama()
    
    def _setup_ollama(self):
        """Set up the Ollama environment and install necessary dependencies."""
        try:
            # Install Ollama
            subprocess.run(["curl", "https://ollama.ai/install.sh", "|", "sh"], shell=True)
            
            # Configure non-interactive frontend
            subprocess.run(["echo", "'debconf debconf/frontend select Noninteractive'", "|", "sudo", "debconf-set-selections"], shell=True)
            
            # Install CUDA drivers
            subprocess.run(["sudo", "apt-get", "update"], shell=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "cuda-drivers"], shell=True)
            
            # Set up NVIDIA library path
            os.environ.update({'LD_LIBRARY_PATH': '/usr/lib64-nvidia'})
            
            # Start Ollama server
            subprocess.Popen(["nohup", "ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Pull the DeepSeek model
            subprocess.run(["ollama", "pull", self.model], shell=True)
            
            # Install Ollama Python package
            subprocess.run(["pip", "install", "ollama"], shell=True)
            
        except Exception as e:
            print(f"Error setting up Ollama: {e}")
            raise
    
    def _single_call(self, prompt: str) -> str:
        """
        Make a single call to the DeepSeek model via Ollama.
        
        Args:
            prompt (str): The prompt to send to the model
            
        Returns:
            str: The model's response
        """
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': "You are a creative and humorous Game Master for a goblin pirate-themed TTRPG."
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            print(f"Error calling DeepSeek model: {e}")
            return "I apologize, but I encountered an error processing your request."
    
    def parse_llm_response(self, response: str) -> str:
        """
        Simple pass-through implementation of the abstract method.
        DeepSeekAgent uses raw text responses and doesn't need structured parsing.
        
        Args:
            response (str): The model's response
            
        Returns:
            str: The unchanged response
        """
        return response

class GeminiAgent(GameMasterAgent):
    """
    A GameMasterAgent implementation that uses Google's Gemini model via AI Studio.
    """
    
    def __init__(self, api_key: str, deep_research: bool = False, max_iterations: int = 3):
        """
        Initialize the GeminiAgent with Google AI Studio configuration.
        
        Args:
            api_key (str): The Google AI Studio API key
            deep_research (bool): Whether to use iterative refinement for responses
            max_iterations (int): Maximum number of refinement iterations
        """
        super().__init__(deep_research=deep_research, max_iterations=max_iterations)
        self.model = "gemini-2.5-pro-exp-03-25"
        self.client = genai.Client(api_key=api_key)
    
    def _single_call(self, prompt: str) -> str:
        """
        Make a single call to the Gemini model via Google AI Studio.
        
        Args:
            prompt (str): The prompt to send to the model
            
        Returns:
            str: The model's response
        """
        try:
            # Create the system message and user message
            messages = [
                {
                    'role': 'system',
                    'content': "You are a creative and humorous Game Master for a goblin pirate-themed TTRPG."
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # Convert messages to Gemini format
            contents = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            # Generate response
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            
            return response.text
            
        except Exception as e:
            print(f"Error calling Gemini model: {e}")
            return "I apologize, but I encountered an error processing your request."
    
    def parse_llm_response(self, response: str) -> str:
        """
        Simple pass-through implementation of the abstract method.
        GeminiAgent uses raw text responses and doesn't need structured parsing.
        
        Args:
            response (str): The model's response
            
        Returns:
            str: The unchanged response
        """
        return response
