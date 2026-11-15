import os
import json
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def ask_gemini(prompt):
    if not GEMINI_API_KEY:
        return None, "Gemini API key is not configured."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2500}
    }
    try:
        response = requests.post(url, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text, None
    except requests.RequestException as exc:
        return None, f"Gemini request failed: {exc}"
    except (KeyError, IndexError, ValueError):
        return None, "The AI returned an unexpected response. Please try again."

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/plan", methods=["POST"])
def create_plan():
    data = request.get_json(silent=True) or {}
    destination = data.get("destination", "").strip()
    if not destination:
        return jsonify({"error": "Please enter a destination."}), 400

    budget = data.get("budget", "Not specified")
    days = data.get("days", "3")
    travelers = data.get("travelers", "1")
    style = data.get("style", "Balanced")
    start_date = data.get("startDate", "Not specified")
    currency = data.get("currency", "INR")

    prompt = f"""
You are a practical, careful travel-planning assistant. Create a personalized trip plan.
Destination: {destination}
Total budget: {budget} {currency}
Duration: {days} days
Number of travelers: {travelers}
Travel style: {style}
Start date: {start_date}

Return a useful, readable response with these exact sections:
1. Trip overview
2. Day-by-day itinerary (morning, afternoon, evening)
3. Estimated budget table with transport, stay, food, activities, and buffer
4. Local food to try
5. Practical travel tips

Keep costs as estimates, clearly label them as estimates, and do not claim live availability,
confirmed prices, bookings, or current opening hours. Mention when transport or entry costs
vary by season. Make the plan fit the stated budget as closely as possible. Use Markdown.
"""
    result, error = ask_gemini(prompt)
    if result:
        return jsonify({"plan": result, "mode": "ai"})
    # Useful demo response so the app can be explored before adding an API key.
    demo = f"""## Your {days}-day trip to {destination}

### 1. Trip overview
A {style.lower()} trip for {travelers} traveler(s), planned around a budget of **{budget} {currency}**.

### 2. Suggested itinerary
"""
    try:
        day_count = max(1, min(10, int(days)))
    except ValueError:
        day_count = 3
    for day in range(1, day_count + 1):
        demo += f"\n**Day {day}**\n- Morning: Explore a well-known local attraction.\n- Afternoon: Enjoy a local food stop and a nearby experience.\n- Evening: Visit a market, viewpoint, or relaxed local area.\n"
    demo += """
### 3. Estimated budget
| Category | Planning estimate |
|---|---:|
| Transport | 30% of budget |
| Accommodation | 30% of budget |
| Food | 20% of budget |
| Activities | 15% of budget |
| Buffer | 5% of budget |

### 4. Local food to try
Ask local residents for popular regional dishes and choose busy, well-reviewed places.

### 5. Practical travel tips
- Check official transport schedules before departure.
- Confirm hotel rates, local permits, and attraction timings directly.
- Keep a small emergency buffer and save offline copies of important bookings.

> Demo mode is active. Add your Gemini API key in the `.env` file to generate destination-specific AI plans.
"""
    return jsonify({"plan": demo, "mode": "demo", "notice": error})

@app.route("/api/chat", methods=["POST"])
def travel_chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    destination = data.get("destination", "the user's trip")
    if not message:
        return jsonify({"error": "Please enter a message."}), 400
    prompt = f"""You are TripMate, a friendly travel assistant. Context: {destination}.
Answer the user's travel question clearly and concisely. Do not invent live prices,
availability, weather, opening hours, or booking confirmations. Tell the user to verify
time-sensitive details with official sources.
User question: {message}"""
    answer, error = ask_gemini(prompt)
    if answer:
        return jsonify({"reply": answer, "mode": "ai"})
    return jsonify({
        "reply": "I’m in demo mode because the Gemini API key is not configured. Add your key to `.env` to enable AI chat. In the meantime, check official tourism and transport websites for current details.",
        "mode": "demo"
    })

if __name__ == "__main__":
    app.run(debug=True)
