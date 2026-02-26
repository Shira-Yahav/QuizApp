import os
import anthropic
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

QUIZ_SCHEMA = {
    "name": "quiz",
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "A short title for the quiz"},
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "Question number starting from 1"},
                        "question": {"type": "string", "description": "The question text"},
                        "options": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The answer options",
                        },
                        "correct_index": {
                            "type": "integer",
                            "description": "Zero-based index of the correct option",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Brief explanation of why the correct answer is right",
                        },
                    },
                    "required": ["id", "question", "options", "correct_index", "explanation"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["title", "questions"],
        "additionalProperties": False,
    },
}

SYSTEM_PROMPT = """You are a quiz generator. Given a user's request, generate a multiple-choice quiz.

Rules:
- Vary difficulty: mix easy, medium, and hard questions
- Make distractors plausible — avoid obviously wrong answers
- Randomize the position of the correct answer across questions (don't always put it first or last)
- Each question must have exactly the number of options the user requests (default 4 if not specified)
- Default to 10 questions if the user doesn't specify a count
- Write clear, unambiguous questions
- Keep explanations concise (1-2 sentences)"""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate_quiz():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Please provide a quiz prompt."}), 400

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "json_schema": QUIZ_SCHEMA,
            },
        )
        import json

        quiz_data = json.loads(response.content[0].text)
        return jsonify(quiz_data)
    except anthropic.APIError as e:
        return jsonify({"error": f"API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Failed to generate quiz: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
