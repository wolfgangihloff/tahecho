from smolagents import OpenAIServerModel

from config import CONFIG


class OpenAIModel:

    def __init__(self):
        self.model = OpenAIServerModel(
            model_id="gpt-4o", api_key=CONFIG["OPENAI_API_KEY"]
        )

    def get_model(self):
        return self.model


openai_model = OpenAIModel().get_model()
