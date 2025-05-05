from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Get API key from environment variable or use default for testing
API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

SYSTEM_MESSAGE = {
    "role": "system",
    "content": """You are HSG AI, a helpful, intelligent, and conversational virtual assistant.
You are designed to answer questions, provide explanations, assist with tasks, and hold meaningful conversations.
Avoid mentioning that you are powered by OpenRouter or any backend technologies.
Stay professional, friendly, and helpful at all times.
If a question is unclear, politely ask for more information.
Always respond as HSG AI."""
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Format messages according to OpenRouter's requirements
    formatted_messages = []
    if history:
        formatted_messages.extend(history)
    formatted_messages.append({"role": "user", "content": user_message})

    headers = {
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "HSG AI Chat",
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",  # Using a more stable model
        "messages": formatted_messages,
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }

    try:
        print("Sending request to OpenRouter with headers:", json.dumps(headers, indent=2))
        print("Payload:", json.dumps(payload, indent=2))
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content: {response.text}")

        if response.status_code == 401:
            error_msg = f"Authorization failed. Response: {response.text}"
            print(error_msg)
            return jsonify({"reply": "Authorization failed. Please check your API key."}), 401
        elif response.status_code == 400:
            error_msg = f"Bad request. Response: {response.text}"
            print(error_msg)
            return jsonify({"reply": "Invalid request format. Please try again."}), 400
        elif response.status_code != 200:
            error_msg = f"Unexpected status code {response.status_code}. Response: {response.text}"
            print(error_msg)
            return jsonify({"reply": "Something went wrong. Please try again later."}), 500

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            error_msg = f"Unexpected response format: {response.text}"
            print(error_msg)
            return jsonify({"reply": "Invalid response from AI service. Please try again."}), 500

        ai_reply = response_data["choices"][0]["message"]["content"]
        return jsonify({"reply": ai_reply})

    except requests.exceptions.Timeout:
        print("Request timed out")
        return jsonify({"reply": "Request timed out. Please try again."}), 504
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"HTTP error occurred: {http_err}\nResponse content: {response.text if 'response' in locals() else 'No response content'}"
        print(error_msg)
        return jsonify({"reply": "Server error. Please try again later."}), 500
    except json.JSONDecodeError as json_err:
        error_msg = f"JSON decode error: {str(json_err)}\nResponse content: {response.text if 'response' in locals() else 'No response content'}"
        print(error_msg)
        return jsonify({"reply": "Invalid response format. Please try again."}), 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return jsonify({"reply": "Something went wrong. Please try again later."}), 500

if __name__ == "__main__":
    app.run(debug=True)
