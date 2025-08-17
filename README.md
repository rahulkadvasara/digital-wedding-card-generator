# Digital Audio Wedding Cards

A full-stack web application for creating, managing, and sharing personalized digital wedding cards with AI-generated audio messages and analytics.

## Features

- **User Authentication:** Secure registration and login with JWT-based authentication.
- **Card Creation:** Users can create wedding cards with custom messages and optional voice samples.
- **AI Voice Generation:** Clone user voices and synthesize personalized audio messages using ElevenLabs API.
- **Analytics:** Track card views and engagement with detailed analytics.
- **QR Code Generation:** Generate QR codes for easy sharing of cards.
- **Frontend:** Responsive HTML/CSS/JS frontend for user interaction.

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
│   ├── utils/ 
├──data/
│   ├── analytics.json
│   ├── cards.json
│   ├── users.json
│   ├── voice_models.json
│   ├── audio/
│   └── qr_codes/
├── frontend/
│   ├── analytics.html
│   ├── create-card.html
│   ├── dashboard.html
│   ├── index.html
│   ├── register.html
│   ├── view-card.html
│   ├── css/
│   └── js/
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
- **Analytics:** `/analytics/track`, `/analytics/card/{card_id}`

See the backend route files for detailed API documentation.

## Development

- **Backend:** FastAPI, Pydantic, JWT, Python-dotenv
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Data Storage:** JSON files (no database required)
