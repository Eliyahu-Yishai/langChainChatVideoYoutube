import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Load environment variables (OPENAI_API_KEY from .env)
load_dotenv()

# Create the chat model
model = ChatOpenAI(
    model="gpt-4o-mini"  # You can change to gpt-4o / gpt-4.1 / etc.
)

SESSIONS_DIR = "sessions"
DEFAULT_SESSION = "default"


def ensure_sessions_dir():
    """Ensure the sessions directory exists."""
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)


def get_session_file(session_name: str) -> str:
    """Get full path for a session's JSON file."""
    safe_name = session_name.replace(" ", "_")
    return os.path.join(SESSIONS_DIR, f"{safe_name}.json")


def create_initial_history():
    """Create the initial conversation history with a system message."""
    return [
        SystemMessage(content="You are a friendly personal assistant. Answer briefly and clearly.")
    ]


def history_to_dicts(history):
    """Convert LangChain messages to a serializable list of dicts."""
    data = []
    for msg in history:
        if isinstance(msg, SystemMessage):
            role = "system"
        elif isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        else:
            continue

        data.append({
            "role": role,
            "content": msg.content
        })
    return data


def dicts_to_history(data):
    """Convert a list of dicts (from JSON) back to LangChain messages."""
    history = []
    for item in data:
        role = item.get("role")
        content = item.get("content", "")

        if role == "system":
            history.append(SystemMessage(content=content))
        elif role == "user":
            history.append(HumanMessage(content=content))
        elif role == "assistant":
            history.append(AIMessage(content=content))

    if not history:
        history = create_initial_history()

    return history


def save_history(history, session_name: str):
    """Save the conversation history to a JSON file for a given session."""
    ensure_sessions_dir()
    data = history_to_dicts(history)
    file_path = get_session_file(session_name)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_history(session_name: str):
    """Load conversation history for a session from JSON if it exists, otherwise create a new one."""
    ensure_sessions_dir()
    file_path = get_session_file(session_name)

    if not os.path.exists(file_path):
        # First time this session is used
        history = create_initial_history()
        save_history(history, session_name)
        return history

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # If file is corrupted, start fresh
        history = create_initial_history()
        save_history(history, session_name)
        return history

    return dicts_to_history(data)


def reset_history(session_name: str):
    """Reset history in memory and on disk for a specific session."""
    history = create_initial_history()
    save_history(history, session_name)
    return history


def list_sessions():
    """Return a list of session names (without .json)."""
    ensure_sessions_dir()
    files = os.listdir(SESSIONS_DIR)
    sessions = [
        os.path.splitext(f)[0]
        for f in files
        if f.endswith(".json")
    ]
    return sessions


def delete_session(session_name: str):
    """Delete a session file if it exists."""
    file_path = get_session_file(session_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def print_help():
    print("\nCommands:")
    print("  exit / quit          - exit the program")
    print("  reset                - reset current session history")
    print("  list                 - list all sessions")
    print("  new <name>           - create a new session and switch to it")
    print("  switch <name>        - switch to an existing session (or create if missing)")
    print("  delete <name>        - delete a session")
    print("  help                 - show this help message\n")


def main():
    print("🔹 Personal Chat with Persistent Multi-Sessions")
    print_help()

    current_session = DEFAULT_SESSION
    history = load_history(current_session)
    print(f"Current session: {current_session}\n")

    while True:
        user_input = input(f"[{current_session}] You: ")

        stripped = user_input.strip()
        command = stripped.lower()

        # Exit program
        if command in ["exit", "quit"]:
            print("Goodbye 👋")
            break

        # Help
        if command == "help":
            print_help()
            continue

        # Reset current session
        if command == "reset":
            history = reset_history(current_session)
            print(f"🔄 Session '{current_session}' has been reset.\n")
            continue

        # List sessions
        if command == "list":
            sessions = list_sessions()
            if not sessions:
                print("No sessions found.\n")
            else:
                print("Sessions:")
                for name in sessions:
                    prefix = "-> " if name == current_session else "   "
                    print(f"{prefix}{name}")
                print()
            continue

        # New session: new <name>
        if command.startswith("new "):
            name = stripped[4:].strip()
            if not name:
                print("Please provide a session name. Example: new work\n")
                continue
            current_session = name
            history = reset_history(current_session)
            print(f"🆕 Created and switched to new session: {current_session}\n")
            continue

        # Switch session: switch <name>
        if command.startswith("switch "):
            name = stripped[7:].strip()
            if not name:
                print("Please provide a session name. Example: switch work\n")
                continue
            current_session = name
            history = load_history(current_session)
            print(f"🔁 Switched to session: {current_session}\n")
            continue

        # Delete session: delete <name>
        if command.startswith("delete "):
            name = stripped[7:].strip()
            if not name:
                print("Please provide a session name. Example: delete work\n")
                continue

            if name == current_session:
                deleted = delete_session(name)
                if deleted:
                    print(f"🗑 Deleted current session '{name}'. Switching back to '{DEFAULT_SESSION}'.\n")
                    current_session = DEFAULT_SESSION
                    history = load_history(current_session)
                else:
                    print(f"Session '{name}' does not exist.\n")
            else:
                deleted = delete_session(name)
                if deleted:
                    print(f"🗑 Deleted session '{name}'.\n")
                else:
                    print(f"Session '{name}' does not exist.\n")
            continue

        # Normal chat message
        history.append(HumanMessage(content=user_input))

        # Get model response based on full history
        response = model.invoke(history)

        print("Assistant:", response.content)
        print()

        # Save assistant response
        history.append(AIMessage(content=response.content))

        # Save updated history for this session
        save_history(history, current_session)


if __name__ == "__main__":
    main()
