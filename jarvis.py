import requests
import speech_recognition as sr
import subprocess
import os
import signal
import time
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
import asyncio
import queue
import threading

# from fcntl import fcntl, F_GETFL, F_SETFL
# from os import O_NONBLOCK, read
# flags = fcntl(p.stdout, F_GETFL) # get current p.stdout flags
# fcntl(p.stdout, F_SETFL, flags | O_NONBLOCK)

booting = 1


def enqueue_output(out, queue):
    while(1):
        time.sleep(1)
        print("Polling")
        queue.put(out.readline())
        #for line in iter(out.readline, b''):
        #    queue.put(line.decode('utf-8'))
    #out.close()
import os

class HearingAid:
    def __init__(self):
        self.hearing_pid = 0
        self.hearing_queue = ""
        self.actual_queue = queue.Queue()
    
    def launch_hearing(self):
        # stdout=PIPE, stderr=STDOUT, stdin=PIPE,
        self.hearing_pid = subprocess.Popen(['python', 'hear.py'], stderr=subprocess.STDOUT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        time.sleep(0.01)
        self.hearing_pid.stdin.write("\n")
        self.stdout_thread = threading.Thread(target=enqueue_output, args=(self.hearing_pid.stdout, self.actual_queue))
        self.stdout_thread.daemon = True
        self.stdout_thread.start()
        
    def hear(self):
        global booting
        #print("hearing")
        if(self.actual_queue.empty()):
            self.hearing_queue = ""
        else:
            self.hearing_queue = self.actual_queue.get()
        if(booting == 1):
            if( "Listening..." in self.hearing_queue):
                booting = 0
                print("booted")
                wait_text = "waiting for wake words '"+wake_word+"'"
                print (wait_text)
                SpeakText(wait_text)
        #print("heard: " + self.hearing_queue)


headers = {
    "Content-Type": "application/json"
}
l_pid = 0
def SpeakText(command):
    p = subprocess.Popen(['python', 'speak.py', '-i', command, '-v', 'Samantha'])
    global l_pid
    l_pid = p.pid

def mic_listen(hearing_aid):
    time.sleep(2)
    hearing_aid.hear()
    return hearing_aid.hearing_queue

def listen_mode(histogram,hearing_aid):
    histogram.clear_if_needed(0)
    break_condition = True
    c = 0
    empty_timeout = "Timeout: No speech detected within the specified time."
    while(break_condition):
        input = mic_listen(hearing_aid)
        if(c > 0):
            if(histogram.current == "" and input == empty_timeout):
                break
            if(len(histogram.current) > 1 and histogram.current[-1] == "?" and input == empty_timeout):
                break
            if(len(histogram.current) > 1 and histogram.current[-1] == "." and input == empty_timeout):
                break
        if(input != empty_timeout):
            histogram.add_to_string(input)
        c = c+1
        if(c > 5):
            break_condition = False

    print("You said: " + histogram.history)
    return histogram.history

def record_text(hearing_aid,histogram):
    global wake_word
    #wait_text = "waiting for wake words '"+wake_word+"'"
    #print (wait_text)
    #SpeakText(wait_text)
    while(1):
        try:
            histogram.add_to_string( mic_listen(hearing_aid) )
            if "Hey Jarvis" in histogram.history:
                if("shut up" in histogram.history):
                    global l_pid
                    try:
                        os.kill(l_pid, signal.SIGTERM)
                    except:
                        print("no process to kill")
                    return "Shutting up"
                SpeakText("Yes sir, how may I help?")
                return listen_mode(histogram,hearing_aid)
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
print ("launch hearing")
aid = HearingAid()
aid.launch_hearing()
while(1):
    histogram.clear_if_needed(0)
    print ("recording text")
    text = record_text(aid, histogram)
    histogram.clear_if_needed(0)
    
    print("create oobabooga request")
    history.append({"role": "user", "content": text})
    response = send_to_oobabooga(history)
    
    print ("speaking response")
    SpeakText(response)
    print(response)