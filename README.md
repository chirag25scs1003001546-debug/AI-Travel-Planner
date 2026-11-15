# TripMate AI — AI Travel Planner

A responsive college project website that uses Generative AI to create personalized travel itineraries and answer travel questions.

## Features
- Responsive landing page and trip planner
- Gemini-powered itinerary generation
- Estimated budget guidance
- Day-wise itinerary, food suggestions, and travel tips
- AI travel assistant chat
- Destination cards that prefill the planner
- Demo mode when no Gemini API key is configured

## Requirements
- Python 3.9+
- Internet connection for Gemini API and remote images/fonts
- Gemini API key from Google AI Studio (optional for demo mode, required for live AI)

## Run on Windows
1. Extract the ZIP file.
2. Open the project folder in VS Code.
3. Open the terminal in that folder.
4. Create a virtual environment:

   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   ```

5. Install packages:

   ```bash
   pip install -r requirements.txt
   ```

6. Copy `.env.example` to a new file named `.env`.
7. Open `.env` and replace `your_gemini_api_key_here` with your own Gemini API key.
8. Start the website:

   ```bash
   python app.py
   ```

9. Open this address in your browser:

   `http://127.0.0.1:5000`

## Run on macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Gemini API key
python app.py
```

Then open `http://127.0.0.1:5000`.

## Gemini API setup
1. Visit https://aistudio.google.com/app/apikey
2. Sign in and create an API key, subject to Google's current availability and terms.
3. Paste the key into `.env`:

   ```env
   GEMINI_API_KEY=your_real_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

4. Restart Flask after changing `.env`.

Never paste your API key into frontend JavaScript, HTML, screenshots, or a public GitHub repository. Keep `.env` private.

## Project structure
```text
ai_travel_planner/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── app.js
```

## How the Generative AI algorithm works
1. The user enters destination, budget, duration, group size, and travel style.
2. The browser sends these values to the Flask backend.
3. Flask creates a structured prompt with the trip details.
4. The backend sends the prompt to the Gemini `generateContent` API.
5. Gemini generates an itinerary and estimated budget guidance.
6. Flask returns the generated text to the browser.
7. JavaScript displays the result on the page.

## Important limitations
- This is a planning assistant, not a booking platform.
- Budget values and recommendations are estimates, not live quotes.
- The project does not check real-time hotel availability, flight fares, weather, or opening hours.
- Verify all important details with official providers before travelling.
- External image and font URLs require an internet connection.
