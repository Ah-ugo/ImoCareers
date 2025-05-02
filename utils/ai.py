import google.generativeai as genai
import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

class AIHelper:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')

    async def generate_cover_letter(self, job: Dict, user: Dict) -> str:
        prompt = f"""
        Generate a professional cover letter for the following job:

        Job Title: {job['title']}
        Company: {job['company']}
        Description: {job['description']}

        Candidate Information:
        Name: {user['name']}
        Skills: {', '.join(user['cv']['skills'])}
        Experience: {len(user['cv']['experience'])} years

        Make it personal, professional, and highlight relevant skills and experience.
        Keep it concise but impactful.
        """

        try:
            response = await self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Failed to generate cover letter: {e}")
            return ""


ai_helper = AIHelper()