import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Loads .env locally. On Render, environment variables are supplied by the service.
load_dotenv()

app = Flask(__name__)


def ask_gemini(prompt):
    """Call Gemini and return (answer, error) without exposing the API key."""
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    model = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()

    if not api_key or api_key == "your_gemini_api_key_here":
        return None, "GEMINI_API_KEY is missing or still set to the example placeholder."

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2500},
    }

    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=45,
        )

        if not response.ok:
            # Read Google's structured error without ever returning the request URL/key.
            try:
                error_data = response.json().get("error", {})
                google_message = error_data.get("message", "No error message supplied.")
                google_status = error_data.get("status", "")
            except (ValueError, AttributeError):
                google_message = "Google returned a non-JSON error response."
                google_status = ""

            return None, (
                f"Gemini API returned HTTP {response.status_code}"
                f"{f' ({google_status})' if google_status else ''}: "
                f"{google_message}"
            )

        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            prompt_feedback = data.get("promptFeedback", {})
            block_reason = prompt_feedback.get("blockReason")
            if block_reason:
                return None, f"Gemini did not generate an answer. Block reason: {block_reason}."
            return None, "Gemini returned no answer candidates."

        parts = candidates[0].get("content", {}).get("parts", [])
        answer = "\n".join(
            part.get("text", "") for part in parts if part.get("text")
        ).strip()

        if not answer:
            return None, "Gemini returned an empty answer."
        return answer, None

    except requests.Timeout:
        return None, "The Gemini request timed out. Please try again."
    except requests.ConnectionError:
        return None, "Could not connect to Google's Gemini API. Check network access."
    except requests.RequestException:
        # Avoid returning exception text because it can contain request details.
        return None, "The request to Gemini failed. Check the Render application logs."
    except ValueError:
        return None, "Gemini returned invalid JSON."


def user_facing_gemini_error(error):
    """Short actionable message suitable for displaying in the chat UI."""
    if not error:
        return "TripMate could not get an answer from Gemini."

    lower = error.lower()
    if "missing" in lower or "placeholder" in lower:
        return (
            "TripMate cannot find GEMINI_API_KEY. In Render, open this web service's "
            "Environment settings, add the exact variable name GEMINI_API_KEY, save, "
            "and redeploy."
        )
    if "http 400" in lower or "http 401" in lower:
        return (
            "Gemini rejected the API request. Check that the Render GEMINI_API_KEY "
            "is a valid, active Google AI Studio key."
        )
    if "http 403" in lower:
        return (
            "Google denied this Gemini API request. Check the API key restrictions, "
            "project/API access, and billing or quota requirements shown in Google AI Studio."
        )
    if "http 404" in lower:
        return (
            "Gemini could not find the configured model. Check the GEMINI_MODEL "
            "value in Render; try gemini-2.5-flash if that model is available to your key."
        )
    if "http 429" in lower:
        return "Gemini rate limit or quota reached. Check your Google AI Studio quota and try again later."
    return f"TripMate could not reach Gemini: {error}"


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

    # Keep the demo fallback, but return a useful diagnostic in the API response.
    demo = f"""## Your {days}-day trip to {destination}

### 1. Trip overview
A {style.lower()} trip for {travelers} traveler(s), planned around a budget of **{budget} {currency}**.

### 2. Suggested itinerary
"""
    try:
        day_count = max(1, min(10, int(days)))
    except (TypeError, ValueError):
        day_count = 3
    for day in range(1, day_count + 1):
        demo += (
            f"\n**Day {day}**\n"
            "- Morning: Explore a well-known local attraction.\n"
            "- Afternoon: Enjoy a local food stop and a nearby experience.\n"
            "- Evening: Visit a market, viewpoint, or relaxed local area.\n"
        )
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
"""
    return jsonify({
        "plan": demo,
        "mode": "demo",
        "notice": error,
        "message": user_facing_gemini_error(error),
    })


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

    app.longer.error("GEMINI CHAT ERROR: %s", error)
    # Return the real failure reason (never the API key) instead of always claiming
    # that the key is missing. This makes the next fix diagnosable from the UI/API.
    return jsonify({
        "reply": user_facing_gemini_error(error),
        "mode": "demo",
        "notice": error,
    })


if __name__ == "__main__":
    app.run(debug=True)
