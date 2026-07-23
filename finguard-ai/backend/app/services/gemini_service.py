import google.generativeai as genai
import time

from app.core.config import settings


genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


async def test_gemini():

    response = model.generate_content(
        "Reply with only: Gemini Connected Successfully"
    )

    return response.text

async def generate_executive_report(prompt: str):

    # print("========== GEMINI FUNCTION CALLED ==========")

    start = time.perf_counter()

    response = model.generate_content(prompt)

    gemini_latency = round(
        (time.perf_counter() - start) * 1000,
        2
    )

    # print("Gemini Latency:", gemini_latency)

    return response.text