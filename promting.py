from dotenv import load_dotenv
import google.generativeai as genai
import os

load_dotenv()  
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content("")
print(response.text)