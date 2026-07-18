# Travel Route Chatbot 🗺️🤖

AI-powered chatbot that recommends travel routes and en-route attractions, with intent recognition and personalized suggestions.

## ✨ Features

- **Conversational AI** — understands user requests through intent recognition (`intent_manager.py`)
- **Smart prompting** — structured prompt engineering for accurate, context-aware responses (`prompt.py`)
- **Travel recommendations** — suggests attractions and routes based on user preferences
- **Web interface** — Flask-served frontend with HTML/JavaScript

## 🛠 Tech Stack

- **Backend:** Python, Flask
- **AI:** Gemini API, LLM-based intent recognition
- **Frontend:** HTML, CSS, JavaScript
- **Testing:** Unit tests for intent and prompt handling

## 📁 Project Structure

```
├── app.py              # Main Flask application
├── config.py           # Configuration
├── intent_manager.py   # Intent recognition logic
├── prompt.py           # Prompt templates and handling
├── routes/             # API route handlers
├── services/           # Business logic and external services
├── templates/          # HTML templates
├── static/             # CSS, JS, assets
├── utils/              # Helper utilities
├── test_intent.py      # Intent recognition tests
└── test_prompt.py      # Prompt handling tests
```

## 🚀 Getting Started

```bash
# Clone the repository
git clone https://github.com/Gunqeq/travel-route-chatbot.git
cd travel-route-chatbot

# Install dependencies
pip install -r requirements.txt

# Set up your API key in config.py or environment variables

# Run the app
python app.py
```

## 🧪 Running Tests

```bash
python test_intent.py
python test_prompt.py
```

## 📸 Screenshots

_(เพิ่ม screenshot หน้าจอ chatbot ตรงนี้)_

## 👤 Author

**Songwut Sudtalai** — [github.com/Gunqeq](https://github.com/Gunqeq)
