from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import re
from typing import Optional

from rgbYoutube import (
    process_youtube_video,
    process_multiple_youtube_videos,
    add_video_to_existing,
    remove_video_and_rebuild,
    query_rag_chain
)

app = FastAPI(title="YouTube Chat AI")

# In-memory storage for the current RAG chain and transcripts
# In production, you'd want to use proper session management
current_rag_chain = None
current_transcripts = {}  # Maps video_id -> transcript_text
current_video_ids = []  # List of loaded video IDs in order


class VideoRequest(BaseModel):
    urls: list[str]  # Changed to support multiple URLs


class AddVideoRequest(BaseModel):
    url: str  # Single URL to add


class RemoveVideoRequest(BaseModel):
    video_id: str  # Video ID to remove


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
    Process one or more YouTube video URLs and build a unified RAG chain
    """
    global current_rag_chain, current_transcripts, current_video_ids

    if not request.urls or len(request.urls) == 0:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one YouTube URL."
        )

    # Extract video IDs from all URLs
    video_ids = []
    invalid_urls = []

    for url in request.urls:
        video_id = extract_video_id(url.strip())
        if video_id:
            video_ids.append(video_id)
        else:
            invalid_urls.append(url)

    if not video_ids:
        raise HTTPException(
            status_code=400,
            detail=f"No valid YouTube URLs found. Invalid URLs: {', '.join(invalid_urls)}"
        )

    # Process all videos and build unified RAG chain
    rag_chain, successful_videos, failed_videos, transcripts_dict = process_multiple_youtube_videos(video_ids)

    if rag_chain is None:
        error_details = "; ".join([f"{v['video_id']}: {v['error']}" for v in failed_videos])
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process videos. Errors: {error_details}"
        )

    # Store the RAG chain and transcripts for this session
    current_rag_chain = rag_chain
    current_transcripts = transcripts_dict
    current_video_ids = successful_videos

    return {
        "success": True,
        "message": f"Processed {len(successful_videos)} video(s) successfully!",
        "video_ids": successful_videos,
        "failed_videos": failed_videos,
        "invalid_urls": invalid_urls
    }


@app.post("/add-video")
async def add_video(request: AddVideoRequest):
    """
    Add a single video to the existing session
    """
    global current_rag_chain, current_transcripts, current_video_ids

    if current_rag_chain is None:
        raise HTTPException(
            status_code=400,
            detail="No initial videos loaded. Please load videos first."
        )

    # Extract video ID from URL
    video_id = extract_video_id(request.url.strip())
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL."
        )

    # Check if video already loaded
    if video_id in current_video_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Video {video_id} is already loaded."
        )

    # Add video to existing transcripts
    rag_chain, success, error, updated_transcripts = add_video_to_existing(
        current_transcripts, video_id
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add video: {error}"
        )

    # Update session storage
    current_rag_chain = rag_chain
    current_transcripts = updated_transcripts
    current_video_ids.append(video_id)

    return {
        "success": True,
        "message": f"Video {video_id} added successfully!",
        "video_id": video_id,
        "video_ids": current_video_ids
    }


@app.post("/remove-video")
async def remove_video(request: RemoveVideoRequest):
    """
    Remove a video from the existing session
    """
    global current_rag_chain, current_transcripts, current_video_ids

    if current_rag_chain is None:
        raise HTTPException(
            status_code=400,
            detail="No videos loaded."
        )

    video_id = request.video_id

    if video_id not in current_video_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Video {video_id} not found in session."
        )

    # Remove video and rebuild
    rag_chain, updated_transcripts, error = remove_video_and_rebuild(
        current_transcripts, video_id
    )

    if error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove video: {error}"
        )

    # Update session storage
    current_rag_chain = rag_chain
    current_transcripts = updated_transcripts
    current_video_ids.remove(video_id)

    return {
        "success": True,
        "message": f"Video {video_id} removed successfully!",
        "video_id": video_id,
        "video_ids": current_video_ids
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
