import google.generativeai as genai
from openai import OpenAI
from config import GEMINI_API_KEY, OPENAI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

class DalleModel:
    def __init__(self, model_name="dall-e-3"):
        self.model_name = model_name

    def generate_image(self, prompt, size="1024x1024", quality="standard", n=1):
        try:
            response = client.images.generate(
                model=self.model_name,
                prompt=prompt,
                size=size,
                quality=quality,
                n=n,
            )
            image_url = response.data[0].url  # Get the URL of the generated image
            return image_url
        except Exception as e:
            print(f"Error generating image: {e}")
            return None


model1 = genai.GenerativeModel("gemini-pro")
model2 = genai.GenerativeModel("gemini-1.5-flash")
model3 = DalleModel("dall-e-2") 
