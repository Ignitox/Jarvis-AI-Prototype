import speech_recognition as sr
import pyttsx3
import requests
import threading
import itertools
import sys
import time
import os

# =========================
# CONFIG
# =========================

API_KEY = "put your api key from open router here"

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
A futuristic AI assistant.
Be smart, concise, professional, and helpful.
"""

memory = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

recognizer = sr.Recognizer()
thinking = False

# =========================
# SPEAK (FIXED)
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
        print("🎤 Listening...")
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
# AI CHAT
# =========================

def ask_jarvis(prompt):
    global memory
    global thinking

    memory.append({
        "role": "user",
        "content": prompt
    })

    data = {
        "model": MODEL,
        "messages": memory
    }

    try:
        thinking = True
        animation_thread = threading.Thread(target=thinking_animation)
        animation_thread.start()

        response = requests.post(
            URL,
            headers=HEADERS,
            json=data
        )

        result = response.json()

        thinking = False
        animation_thread.join()

        if "choices" in result:
            reply = result["choices"][0]["message"]["content"]

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
# MAIN LOOP
# =========================

def main():
    mode = "text"

    speak("Jarvis online.")

    while True:

        if mode == "text":
            command = input("You: ").strip().lower()

            if command == "`":
                print("Shutting down...")
                os._exit(0)

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
            reply = ask_jarvis(command)
            speak(reply)

# =========================
# START
# =========================

if __name__ == "__main__":
    main()