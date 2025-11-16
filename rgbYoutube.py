from dotenv import load_dotenv
import os

from youtube_transcript_api import YouTubeTranscriptApi

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


# -------- 1. Load API key --------
load_dotenv()  # expects OPENAI_API_KEY in .env


# -------- 2. Get YouTube transcript --------
def get_youtube_transcript(video_id: str) -> str:
    """
    Download transcript for a given YouTube video (if available)
    and return it as a single long text.
    """
    ytt_api = YouTubeTranscriptApi()
    fetched = ytt_api.fetch(video_id, languages=['en'])  # אפשר גם ['he', 'en']

    # fetched הוא FetchedTranscript - אפשר ללכת על snippet.text
    lines = [snippet.text for snippet in fetched if snippet.text.strip()]
    full_text = "\n".join(lines)
    return full_text


# -------- 3. Build RAG components from transcript --------
def build_rag_from_text(text: str):
    # Split the transcript into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    docs = splitter.create_documents([text])

    # Create embeddings + vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # Build RAG chain: retriever -> prompt -> model -> string
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an assistant that answers ONLY based on the given video transcript context. "
            "If the answer is not in the transcript, say: 'Not found in the video transcript.'"
        ),
        (
            "user",
            "Question: {question}\n\n"
            "Relevant transcript parts:\n{context}"
        )
    ])

    model = ChatOpenAI(model="gpt-4o-mini")

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )

    return rag_chain


# -------- 4. Process video and create RAG chain --------
def process_youtube_video(video_id: str):
    """
    Process a YouTube video and return a RAG chain for querying.
    Returns (rag_chain, error_message).
    If successful, rag_chain is not None and error_message is None.
    If failed, rag_chain is None and error_message contains the error.
    """
    try:
        transcript_text = get_youtube_transcript(video_id)
    except Exception as e:
        return None, f"Failed to download transcript: {str(e)}"

    if not transcript_text.strip():
        return None, "Transcript is empty or unavailable."

    try:
        rag_chain = build_rag_from_text(transcript_text)
        return rag_chain, None
    except Exception as e:
        return None, f"Failed to build RAG chain: {str(e)}"


# -------- 5. Process multiple YouTube videos --------
def process_multiple_youtube_videos(video_ids: list):
    """
    Process multiple YouTube videos and create a unified RAG chain.
    Returns (rag_chain, successful_videos, failed_videos, transcripts_dict).
    transcripts_dict maps video_id -> transcript_text for successful videos.
    """
    successful_videos = []
    failed_videos = []
    all_transcripts = []
    transcripts_dict = {}

    for video_id in video_ids:
        try:
            transcript_text = get_youtube_transcript(video_id)
            if transcript_text.strip():
                all_transcripts.append(transcript_text)
                successful_videos.append(video_id)
                transcripts_dict[video_id] = transcript_text
            else:
                failed_videos.append({"video_id": video_id, "error": "Transcript is empty"})
        except Exception as e:
            failed_videos.append({"video_id": video_id, "error": str(e)})

    if not all_transcripts:
        return None, [], failed_videos, {}

    # Combine all transcripts into one text
    combined_text = "\n\n--- NEW VIDEO ---\n\n".join(all_transcripts)

    try:
        rag_chain = build_rag_from_text(combined_text)
        return rag_chain, successful_videos, failed_videos, transcripts_dict
    except Exception as e:
        return None, successful_videos, failed_videos + [{"error": f"Failed to build RAG chain: {str(e)}"}], transcripts_dict


# -------- 5b. Add single video to existing transcripts --------
def add_video_to_existing(transcripts_dict: dict, new_video_id: str):
    """
    Add a new video to existing transcripts and rebuild RAG chain.
    Returns (rag_chain, success, error_message, updated_transcripts_dict).
    """
    try:
        transcript_text = get_youtube_transcript(new_video_id)
        if not transcript_text.strip():
            return None, False, "Transcript is empty", transcripts_dict

        # Add new transcript to dictionary
        updated_transcripts = transcripts_dict.copy()
        updated_transcripts[new_video_id] = transcript_text

        # Combine all transcripts
        all_transcripts = list(updated_transcripts.values())
        combined_text = "\n\n--- NEW VIDEO ---\n\n".join(all_transcripts)

        # Build new RAG chain
        rag_chain = build_rag_from_text(combined_text)
        return rag_chain, True, None, updated_transcripts

    except Exception as e:
        return None, False, str(e), transcripts_dict


# -------- 5c. Remove video and rebuild RAG chain --------
def remove_video_and_rebuild(transcripts_dict: dict, video_id_to_remove: str):
    """
    Remove a video from transcripts and rebuild RAG chain.
    Returns (rag_chain, updated_transcripts_dict, error_message).
    """
    if video_id_to_remove not in transcripts_dict:
        return None, transcripts_dict, f"Video {video_id_to_remove} not found"

    # Remove the video
    updated_transcripts = transcripts_dict.copy()
    del updated_transcripts[video_id_to_remove]

    if not updated_transcripts:
        return None, {}, "Cannot remove last video"

    try:
        # Combine remaining transcripts
        all_transcripts = list(updated_transcripts.values())
        combined_text = "\n\n--- NEW VIDEO ---\n\n".join(all_transcripts)

        # Build new RAG chain
        rag_chain = build_rag_from_text(combined_text)
        return rag_chain, updated_transcripts, None

    except Exception as e:
        return None, transcripts_dict, f"Failed to rebuild RAG chain: {str(e)}"


# -------- 6. Query the RAG chain --------
def query_rag_chain(rag_chain, question: str):
    """
    Query the RAG chain with a question.
    Returns (answer, error_message).
    """
    try:
        answer = rag_chain.invoke(question)
        return answer, None
    except Exception as e:
        return None, f"Error while querying: {str(e)}"


# -------- 7. CLI Chat loop (original functionality) --------
def chat_over_youtube(video_id: str):
    print(f"🎥 Building RAG for YouTube video: {video_id}")
    print("Downloading transcript...")

    rag_chain, error = process_youtube_video(video_id)
    if error:
        print(error)
        return

    print("✅ Ready!")
    print("Ask anything about this YouTube video.")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("You: ")

        if question.strip().lower() == "exit":
            print("Goodbye!")
            break

        answer, error = query_rag_chain(rag_chain, question)
        if error:
            print("Error:", error)
            continue

        print("AI:", answer)
        print()


if __name__ == "__main__":
    # Example: replace with your own video ID
    # For URL https://www.youtube.com/watch?v=ABC123XYZ  ->  video_id = "ABC123XYZ"
    video_id = "lkIFF4maKMU"

    chat_over_youtube(video_id)
