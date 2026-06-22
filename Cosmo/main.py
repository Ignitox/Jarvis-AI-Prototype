import speech_recognition as sr
import pyttsx3
import requests
import threading
import itertools
import sys
import time
import os
import webbrowser
import urllib.parse
import wikipedia
import json

from datetime import datetime
from duckduckgo_search import DDGS

# =========================
# CONFIG
# =========================

API_KEY = "put your api key here"

MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"

URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "Jarvis"
}

SYSTEM_PROMPT = """
You are Jarvis.
A highly intelligent personal butler AI.

Rules:
- Be concise.
- Be helpful.
- Be natural.
- Be smart.
- Summarize facts clearly.
- Never dump raw search snippets.
- Never output JSON/tool syntax.
"""

memory = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

recognizer = sr.Recognizer()
thinking = False
last_query = ""

# =========================
# SPEAK
# =========================

def speak(text):
    print(f"\nJarvis: {text}\n")

    engine = pyttsx3.init()
    engine.setProperty("rate", 180)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# =========================
# LISTEN
# =========================

def listen():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)

        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            print(f"You: {text}")
            return text.lower()
        except:
            return ""

# =========================
# THINKING ANIMATION
# =========================

def thinking_animation():
    global thinking

    for frame in itertools.cycle([
        "Thinking.",
        "Thinking..",
        "Thinking..."
    ]):
        if not thinking:
            break

        sys.stdout.write("\r" + frame)
        sys.stdout.flush()
        time.sleep(0.4)

    sys.stdout.write("\r" + " " * 30 + "\r")

# =========================
# SMART SEARCH
# =========================

def web_search(query):
    try:
        results_text = []

        refined_query = f'"{query}"'

        with DDGS() as ddgs:
            results = list(ddgs.text(refined_query, max_results=8))

        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")

            if title or body:
                results_text.append(
                    f"{title}: {body}"
                )

        wiki_summary = ""
        try:
            wiki_summary = wikipedia.summary(query, sentences=2)
        except:
            pass

        combined = ""

        if wiki_summary:
            combined += wiki_summary + "\n\n"

        if results_text:
            combined += "\n".join(results_text[:5])

        if combined.strip() == "":
            combined = f"No useful results found for {query}."

        return combined

    except Exception as e:
        return f"Search failed: {str(e)}"

# =========================
# SEARCH DETECTION
# =========================

def detect_search_needed(command):
    triggers = [
        "who is",
        "whos",
        "what is",
        "where is",
        "when is",
        "tell me about",
        "search",
        "find"
    ]

    return any(command.startswith(t) for t in triggers)

# =========================
# AI CHAT
# =========================

def ask_jarvis(prompt):
    global memory
    global thinking

    memory.append({
        "role": "user",
        "content": prompt
    })

    try:
        thinking = True
        animation_thread = threading.Thread(
            target=thinking_animation
        )
        animation_thread.start()

        response = requests.post(
            URL,
            headers=HEADERS,
            json={
                "model": MODEL,
                "messages": memory
            }
        )

        result = response.json()

        thinking = False
        animation_thread.join()

        if "choices" in result:
            reply = result["choices"][0]["message"]["content"]

            # Prevent tool JSON
            if reply.strip().startswith("{"):
                try:
                    tool_data = json.loads(reply)

                    if tool_data.get("type") == "search":
                        query = tool_data.get(
                            "query",
                            prompt
                        )

                        search_result = web_search(query)

                        return ask_jarvis(
                            f"Summarize clearly:\n{search_result}"
                        )

                except:
                    pass

            memory.append({
                "role": "assistant",
                "content": reply
            })

            return reply

        elif "error" in result:
            return f"API Error: {result['error']['message']}"

        return "Unknown response."

    except Exception as e:
        thinking = False
        return f"Error: {e}"

# =========================
# COMMAND HANDLER
# =========================

def process_command(command):
    global last_query

    command = command.lower().strip()

    # quit
    if command == "`" or command == "quit":
        speak("Shutting down.")
        os._exit(0)

    # time
    if "time" in command:
        return f"The current time is {datetime.now().strftime('%I:%M %p')}"

    # date
    if "date" in command:
        return f"Today's date is {datetime.now().strftime('%d %B %Y')}"

    # open sites
    if command == "open youtube":
        webbrowser.open("https://youtube.com")
        return "Opening YouTube."

    if command == "open google":
        webbrowser.open("https://google.com")
        return "Opening Google."

    # youtube search
    if command.startswith("youtube "):
        query = command.replace("youtube ", "")
        last_query = query

        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(url)

        return f"Searching YouTube for {query}"

    # continue last search on youtube
    if command == "on youtube" and last_query:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(last_query)}"
        webbrowser.open(url)

        return f"Searching YouTube for {last_query}"

    # channel lookup
    if command == "channel" and last_query:
        query = f"{last_query} youtube channel"

        search_data = web_search(query)

        return ask_jarvis(
            f"Summarize this channel:\n{search_data}"
        )

    # youtube handle lookup
    if "@" in command and ("yt" in command or "youtube" in command):
        handle = ""

        for word in command.split():
            if word.startswith("@"):
                handle = word
                break

        if handle:
            last_query = handle

            search_data = web_search(
                f"{handle} youtube channel"
            )

            return ask_jarvis(
                f"""
Summarize this YouTube channel clearly:

{search_data}

Explain:
- Who they are
- What content they make
"""
            )

    # factual searches
    if detect_search_needed(command):
        last_query = command

        search_data = web_search(command)

        return ask_jarvis(
            f"Summarize this clearly:\n{search_data}"
        )

    # normal AI chat
    last_query = command
    return ask_jarvis(command)

# =========================
# TERMINAL MODE
# =========================

def terminal_mode():
    mode = "text"

    speak("Jarvis online.")

    while True:

        if mode == "text":
            command = input("You: ").strip().lower()

            if command == "voice":
                mode = "voice"
                print("Voice mode enabled.")
                continue

        else:
            command = listen()

            if command == "text":
                mode = "text"
                print("Text mode enabled.")
                continue

        if command:
            reply = process_command(command)
            speak(reply)

# =========================
# START
# =========================

if __name__ == "__main__":
    terminal_mode()