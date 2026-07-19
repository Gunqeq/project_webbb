# Travel Route Chatbot 🗺️🤖

AI-powered travel chatbot on **LINE**. Tell it where you want to go — it understands your request, then recommends routes and attractions along the way, complete with maps and live weather.

## ✨ Features

- **Chat naturally on LINE** — built on the LINE Messaging API with webhook integration and quick replies
- **Intent recognition** — Gemini AI figures out what the user wants (find a route, get attractions, check weather) before answering
- **Smart route suggestions** — combines Google Maps data with en-route attraction recommendations
- **Live weather** — pulls current conditions from OpenWeather so users know what to expect
- **Interactive map view** — LIFF page shows the suggested route visually inside LINE
- **Tested** — unit tests cover intent recognition and prompt handling

## 🛠 Tech Stack

| Layer     | Technology                                   |
| --------- | -------------------------------------------- |
| Backend   | Python, Flask                                |
| AI        | Google Gemini API                            |
| Messaging | LINE Messaging API, LIFF                     |
| Data      | Google Maps API, OpenWeather API             |
| Frontend  | HTML, CSS, JavaScript                        |

## 📁 Project Structure

```
├── app.py               # Main Flask app + LINE webhook handler
├── config.py            # Loads API keys from environment variables
├── intent_manager.py    # Detects user intent from messages
├── prompt.py            # Prompt templates for Gemini
├── routes/              # API endpoints
├── services/            # Gemini, route, province, and logging services
├── utils/               # Maps, weather, and helper utilities
├── templates/           # Web and LIFF pages
├── test_intent.py       # Intent recognition tests
└── test_prompt.py       # Prompt handling tests
```

## 🚀 Getting Started

```bash
# Clone the repository
git clone https://github.com/Gunqeq/travel-route-chatbot.git
cd travel-route-chatbot

# Install dependencies
pip install -r requirements.txt

# Create a .env file with your keys:
#   LINE_CHANNEL_SECRET=...
#   LINE_CHANNEL_ACCESS_TOKEN=...
#   GEMINI_API_KEY=...
#   GOOGLE_MAPS_API_KEY=...
#   OPENWEATHER_API_KEY=...

# Run the app
python app.py
```

## 🧪 Running Tests

```bash
python test_intent.py
python test_prompt.py
```

## 📸 Screenshots

<img width="1374" height="989" alt="สกรีนช็อต 2025-10-21 184812" src="https://github.com/user-attachments/assets/21f565e4-867f-44b4-86cd-aebbf0f0c94a" />


## 👤 Author

**Songwut Sudtalai** — [github.com/Gunqeq](https://github.com/Gunqeq)

> Built during my internship at Innovate AI Co., Ltd.
