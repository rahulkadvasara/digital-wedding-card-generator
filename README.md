# Digital Audio Wedding Cards

A simple web application for creating personalized digital wedding cards with AI-generated audio messages.

## Features

- **User Authentication:** Simple registration and login system.
- **Card Creation:** Create wedding cards with custom messages and voice samples.
- **AI Voice Generation:** Clone user voices and synthesize personalized audio messages using ElevenLabs API.
- **Card Sharing:** Share cards via direct links.

## Project Structure

```
.
├── .env
├── .gitignore
├── README.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/ 
├── data/
│   ├── cards.json
│   ├── users.json
│   └── audio/
└── frontend/
    ├── create-card.html
    ├── dashboard.html
    ├── index.html
    ├── register.html
    ├── view-card.html
    ├── css/
    └── js/
```

## Getting Started

### Prerequisites

- Python 3.10+
- [ElevenLabs API key](https://elevenlabs.io/) for voice generation

### Setup

1. **Clone the repository:**
    ```sh
    git clone <repo-url>
    cd digital wedding card
    ```

2. **Backend Setup:**
    - Create a `.env` file in the root directory. Example:
        ```
        JWT_SECRET=your-secret-key
        ELEVENLABS_API_KEY=your-elevenlabs-api-key
        ```
    - Install dependencies:
        ```sh
        cd backend
        pip install -r requirements.txt
        ```

3. **Frontend Setup:**
    - No build step required for static HTML/JS/CSS.
    - Update API URLs in `frontend/js/auth.js` and other JS files if needed.

4. **Run the Backend Server:**
    ```sh
    cd backend
    python .\main.py
    ```

5. **Access the Application:**
    - Open `frontend/index.html` in your browser, or serve the `frontend/` directory using a static file server.
    - Backend API runs at `http://localhost:8000`.

## API Overview

- **Authentication:** `/auth/login`, `/auth/register`
- **Cards:** `/cards/create`, `/cards/{card_id}`, `/cards/my-cards`
- **Voice:** `/voice/clone`, `/voice/synthesize`

## Development

- **Backend:** FastAPI, Pydantic, JWT, Python-dotenv
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Data Storage:** JSON files (no database required)
