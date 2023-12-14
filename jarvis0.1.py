from whisper_mic import WhisperMic
import requests
import speech_recognition as sr
import pyttsx3
import base64
import json

r = sr.Recognizer()

url = "http://127.0.0.1:5000/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

# def SpeakText(command):
#     engine = pyttsx3.init()
#     engine.say(command)
#     engine.runAndWait()

# def record_text():
#     while(1):
#         try:
#             mic = WhisperMic()
#             result = mic.listen()

#             if "Hey Jarvis" in result:
#                 SpeakText("Yes sir, how may I help?")
#                 # print("Wake word detected. Listening...")
#                 result = mic.listen()
#                 print("You said: " + result)
#                 return result
#             else:
#                 print("Wake word not detected. Please say 'Hey Jarvis' to activate.")

#         except sr.RequestError as e:
#                 print("Could not request results; {0}".format(e))
#         except sr.UnknownValueError:
#                 print("unknown error occured")

def send_to_oobabooga(messages):
    data = {
        "mode": "chat",
        "character": "Jarvis",
        "messages": messages
    }

    response = requests.post(url, headers=headers, json=data, verify=False)
    reply = response.json()['choices'][0]['message']['content']
    return reply

history = []
with open('jarvis.gif', 'rb') as f:
    corpo = f.read()
    gif = base64.b64encode(corpo).decode('utf-8')
    history.append({"role": "user", "content": gif})
    response = send_to_oobabooga(history)
    print(response)

# while(1):
#     text = record_text()
#     history.append({"role": "user", "content": text})
#     response = send_to_oobabooga(corpo)
#     SpeakText(response)
