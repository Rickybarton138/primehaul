# PrimeHaul OS

An AI-powered web application for generating instant moving quotes with automated inventory detection.

## Features

- Interactive map-based location selection (Mapbox)
- Multi-room inventory management
- AI-powered photo analysis using OpenAI Vision API
- Automatic item detection and categorization
- Real-time quote estimation

## Setup

### 1. Prerequisites

- Python 3.12+
- OpenAI API key
- Mapbox access token

### 2. Installation

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add:
- Your Mapbox access token
- Your OpenAI API key

### 4. Run the application

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://localhost:8000`

## Technology Stack

- **Backend**: FastAPI, Python 3.12
- **AI**: OpenAI GPT-4o-mini (Vision API)
- **Frontend**: Jinja2 templates, vanilla JavaScript
- **Maps**: Mapbox GL JS
- **File handling**: aiofiles, Pillow

## Project Structure

```
primehaul-os/
├── app/
│   ├── main.py           # FastAPI application
│   ├── ai_vision.py      # OpenAI Vision integration
│   ├── static/           # CSS, images, uploaded photos
│   └── templates/        # Jinja2 HTML templates
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md
```

## API Endpoints

- `GET /` - Redirect to demo survey
- `GET /s/{token}` - Start survey
- `POST /s/{token}/move` - Set pickup/dropoff locations
- `POST /s/{token}/property` - Set property type
- `POST /s/{token}/rooms/add` - Add room
- `POST /s/{token}/room/{room_id}/upload` - Upload photos & analyze with AI
- `GET /s/{token}/quote-preview` - View quote

## Security Features

- File upload validation (type and size limits)
- CORS middleware
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Input sanitization
- Error handling and logging

## Development Notes

- State is stored in-memory (not persistent across restarts)
- For production, implement proper database storage
- Configure CORS origins for production deployment
- Set up proper secrets management
- Consider adding rate limiting for API endpoints

## License

Proprietary
