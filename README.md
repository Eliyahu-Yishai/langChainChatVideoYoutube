# YouTube Chat AI

An intelligent chatbot application that allows you to ask questions about YouTube videos using RAG (Retrieval-Augmented Generation) technology powered by LangChain and OpenAI.

## Features

- 🎥 Load multiple YouTube videos at once
- 💬 Ask questions about video content
- ➕ Add new videos during chat without losing history
- ➖ Remove specific videos from active session
- 🔄 Unified knowledge base across all loaded videos
- 🎨 Clean, responsive web interface
- 🐳 Docker support for easy deployment

## Prerequisites

- Python 3.11+ (for local development)
- Docker and Docker Compose (for containerized deployment)
- OpenAI API Key

## Quick Start with Docker

### 1. Clone and Setup

```bash
cd langChainPoc
```

### 2. Create .env file

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

The application will be available at **http://localhost:8000**

### 4. View Logs

```bash
docker-compose logs -f
```

### 5. Stop the Application

```bash
docker-compose down
```

## Local Development Setup

### 1. Create Virtual Environment

```bash
python -m venv .venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
.\.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create .env File

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Run the Application

```bash
python app.py
```

Open your browser at **http://localhost:8000**

## Docker Commands

### Build Image

```bash
docker build -t youtube-chat-ai .
```

### Run Container

```bash
docker run -d \
  --name youtube-chat-ai \
  -p 8000:8000 \
  --env-file .env \
  youtube-chat-ai
```

### View Container Logs

```bash
docker logs -f youtube-chat-ai
```

### Stop and Remove Container

```bash
docker stop youtube-chat-ai
docker rm youtube-chat-ai
```

## Usage

### 1. Load Videos

- Enter one or more YouTube URLs (one per input field)
- Click "+ Add Another Video" to add more input fields
- Click "Load Videos" to process all videos

### 2. Chat with Videos

- Ask questions about the video content
- The AI will answer based on the transcripts

### 3. Manage Videos During Chat

- Click "Manage ▼" to expand video management
- **Add new videos**: Paste URL and click "+ Add"
- **Remove videos**: Click the "×" button next to any video
- Management UI auto-collapses after operations

### 4. Start Over

- Click "Start Over" to return to the initial screen
- Load a new set of videos

## Project Structure

```
langChainPoc/
├── app.py                  # FastAPI backend server
├── rgbYoutube.py          # YouTube transcript & RAG logic
├── static/
│   ├── index.html         # Frontend UI
│   ├── script.js          # Frontend logic
│   └── style.css          # Styling
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose configuration
├── .dockerignore         # Files to exclude from Docker
├── .env                  # Environment variables (create this)
└── README.md            # This file
```

## Technology Stack

- **Backend**: FastAPI, Python 3.11
- **AI/ML**: LangChain, OpenAI GPT-4
- **Vector Store**: ChromaDB
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Video Processing**: YouTube Transcript API
- **Containerization**: Docker, Docker Compose

## API Endpoints

- `GET /` - Serve web interface
- `POST /process-video` - Load initial videos
- `POST /add-video` - Add video to session
- `POST /remove-video` - Remove video from session
- `POST /chat` - Send question and get answer
- `GET /health` - Health check endpoint

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |

## Troubleshooting

### Port 8000 Already in Use

**Windows:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -ti:8000 | xargs kill -9
```

### Docker Build Issues

```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### OpenAI API Errors

- Verify your API key is correct in `.env`
- Check your OpenAI account has credits
- Ensure API key has proper permissions

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
