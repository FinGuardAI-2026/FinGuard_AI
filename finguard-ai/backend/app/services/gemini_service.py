import google.generativeai as genai

from app.core.config import settings


genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


async def test_gemini():

    response = model.generate_content(
        "Reply with only: Gemini Connected Successfully"
    )

    return response.text

async def generate_executive_report(prompt: str):

    response = model.generate_content(prompt)

    return response.text