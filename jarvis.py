from whisper_mic import WhisperMic
import requests
import speech_recognition as sr
import subprocess
import os
import signal
r = sr.Recognizer()

url = "http://127.0.0.1:5000/v1/chat/completions"

wake_word = "Hey Jarvis"


class StringHistory:
    def __init__(self):
        self.history = ""
        self.current = ""
        self._counter = 0

    def add_to_string(self, value):
        """Adds value to string1 and resets string2"""
        print ("Heard: (" + value + ")")
        self.history += value
        self.current = value
        self._counter += 1

    def clear_if_needed(self, threshold):
        """Clears string1 and resets counter if counter >= threshold"""
        if self._counter >= threshold:
            self.history = ""
            self._counter = 0

    def __str__(self):
        return f"history: {self.history}, current: {self.current}, Counter: {self._counter}"

headers = {
    "Content-Type": "application/json"
}
l_pid = 0
def SpeakText(command):
    p = subprocess.Popen(['python', 'speak.py', '-i', command, '-v', 'Samantha'])
    global l_pid
    l_pid = p.pid

def listen_mode(histogram,mic):
    histogram.clear_if_needed(0)
    break_condition = True
    c = 0
    empty_timeout = "Timeout: No speech detected within the specified time."
    while(break_condition):
        input = mic.listen(2)
        if(c > 0):
            if(histogram.current == "" and input == empty_timeout):
                break
            if(histogram.current[-1] == "?" and input == empty_timeout):
                break
            if(histogram.current[-1] == "." and input == empty_timeout):
                break
        if(input != empty_timeout):
            histogram.add_to_string(input)
        c = c+1
        if(c > 5):
            break_condition = False

    print("You said: " + histogram.history)
    return histogram.history

def record_text(mic,histogram):
    global wake_word
    wait_text = "waiting for wake words '"+wake_word+"'"
    print (wait_text)
    SpeakText(wait_text)
    while(1):
        try:
            histogram.add_to_string( mic.listen(1.5) )
            if "Hey Jarvis" in histogram.history:
                if("shut up" in histogram.history):
                    global l_pid
                    try:
                        os.kill(l_pid, signal.SIGTERM)
                    except:
                        print("no process to kill")
                    return "Shutting up"
                SpeakText("Yes sir, how may I help?")
                return listen_mode(histogram,mic)
            histogram.clear_if_needed(2)
        except sr.RequestError as e:
                print("Could not request results; {0}".format(e))
        except sr.UnknownValueError:
                print("unknown error occured")

def send_to_oobabooga(messages):
    data = {
        "mode": "chat",
        "character": "Assistant",
        "messages": messages
    }

    response = requests.post(url, headers=headers, json=data, verify=False)
    try:
        reply = response.json()['choices'][0]['message']['content']
    except:
        try:
            reply = response.json()
        except:
            reply = "Something went terribly wrong."
            print(response)
    return reply

history = []
print ("init histogram")
histogram = StringHistory()
print ("init mic")
mic = WhisperMic()
while(1):
    histogram.clear_if_needed(0)
    print ("recording text")
    text = record_text(mic, histogram)
    histogram.clear_if_needed(0)
    
    print("create oobabooga request")
    history.append({"role": "user", "content": text})
    response = send_to_oobabooga(history)
    
    print ("speaking response")
    SpeakText(response)
    print(response)