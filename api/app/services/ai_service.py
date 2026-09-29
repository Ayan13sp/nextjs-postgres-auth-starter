import json
import os
from groq import AsyncGroq 
from app.core.config import settings

async def get_ai_evaluation(model_answer: str, student_answer: str) -> dict:
    """
    Compares a student's answer to a model answer using the Groq LLM.

    Returns:
        A dictionary with 'score' and 'feedback'.
    """
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "score": -1,
            "feedback": "GROQ_API_KEY is not set. Please add GROQ_API_KEY to your Render environment variables."
        }

    system_prompt = """
    You are an expert AI evaluator for an online learning platform. Your task is to evaluate a student's answer based on a model answer provided by the teacher.

    You must provide two things in your response:
    1.  A 'score' from 0 to 10. The score should reflect how well the student's answer matches the key concepts of the model answer.
    2.  A 'feedback' string. The feedback should be constructive, personalized, and written directly to the student. Explain what they did well and what they can improve.

    Respond ONLY with a valid JSON object in the following format:
    {"score": <integer>, "feedback": "<string>"}
    """

    try:
        client = AsyncGroq(api_key=api_key)
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": f'Please evaluate the following submission:\n\n**Model Answer:** "{model_answer}"\n\n**Student\'s Answer:** "{student_answer}"',
                },
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        
        response_content = chat_completion.choices[0].message.content.strip()
        if response_content.startswith("```"):
            lines = response_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response_content = "\n".join(lines).strip()

        result = json.loads(response_content)
        score = int(result.get("score", 0))
        score = max(0, min(10, score))
        feedback = str(result.get("feedback", "No feedback provided."))
        return {"score": score, "feedback": feedback}

    except Exception as e:
        print(f"An error occurred during AI evaluation: {e}")
        return {
            "score": -1,
            "feedback": f"AI evaluation error ({type(e).__name__}): {str(e)}"
        }
