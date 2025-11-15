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


# -------- 5. Query the RAG chain --------
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


# -------- 6. CLI Chat loop (original functionality) --------
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
