from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import re
from typing import Optional

from rgbYoutube import process_youtube_video, query_rag_chain

app = FastAPI(title="YouTube Chat AI")

# In-memory storage for the current RAG chain
# In production, you'd want to use proper session management
current_rag_chain = None


class VideoRequest(BaseModel):
    url: str


class ChatRequest(BaseModel):
    question: str


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/.*[?&]v=)([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # If it's already just the video ID (11 characters)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url

    return None


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")


@app.post("/process-video")
async def process_video(request: VideoRequest):
    """
    Process a YouTube video URL and build the RAG chain
    """
    global current_rag_chain

    video_id = extract_video_id(request.url)
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL. Please provide a valid YouTube video link."
        )

    # Process the video and build RAG chain
    rag_chain, error = process_youtube_video(video_id)

    if error:
        raise HTTPException(status_code=500, detail=error)

    # Store the RAG chain for this session
    current_rag_chain = rag_chain

    return {
        "success": True,
        "message": f"Video processed successfully! (ID: {video_id})",
        "video_id": video_id
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Send a question and get an AI response based on the current video
    """
    global current_rag_chain

    if current_rag_chain is None:
        raise HTTPException(
            status_code=400,
            detail="No video has been processed yet. Please provide a YouTube URL first."
        )

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Query the RAG chain
    answer, error = query_rag_chain(current_rag_chain, request.question)

    if error:
        raise HTTPException(status_code=500, detail=error)

    return {
        "answer": answer,
        "question": request.question
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "video_loaded": current_rag_chain is not None
    }


# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    print("Starting YouTube Chat AI server...")
    print("Open your browser at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
