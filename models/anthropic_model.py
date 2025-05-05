import os
from smolagents import OpenAIServerModel, LiteLLMModel

class AnthropicModel: 
    def __init__(self):
        self.model = OpenAIServerModel(
            model_id="openrouter/anthropic/claude-3-sonnet",
            api_base="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        
    def get_model(self):
        return self.model
    
        
anthropic_model = AnthropicModel().get_model()