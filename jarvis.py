import requests
import speech_recognition as sr
import subprocess
import os
import signal
import time
r = sr.Recognizer()

url = "http://127.0.0.1:5000/v1/chat/completions"

Character= "Jarvis" # If you didn't install Jarvis.yaml change this to assistant.

wake_word = "Jarvis"
kill_words = ["shut up","nevermind","never mind","stop","cancel","quit","exit","end","shut it","shut it down","shut down","shut it down"]


class StringHistory:
    def __init__(self):
        self.history = ""
        self.current = ""
        self._counter = 0

    def add_to_string(self, value):
        """Adds value to string1 and resets string2"""
        #print ("Heard: (" + value + ")")
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

import queue
import threading

booting = 1

def enqueue_output(out, queue):
    while(1):
        time.sleep(1)
        print("Polling")
        for line in iter(out.readline, b''):
            queue.put(line)

import os # Not sure if this is still needed.

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
            self.hearing_queue = ""
            while (not self.actual_queue.empty()):
                self.hearing_queue += self.actual_queue.get()
            
        if(booting == 1):
            if( "Listening..." in self.hearing_queue):
                booting = 0
                print("booted")
                wait_text = "waiting for wake words '"+wake_word+"'"
                print (wait_text)
                SpeakText(wait_text)
        #print("heard: " + self.hearing_queue)

class ThinkingAid:
    def __init__(self):
        self.pids = []
        self.queue = ""
        self.actual_queue = queue.Queue()
        self.command = None

    def launch(self, command):
        global Character
        global url
        self.command = command
        self.pids.append( subprocess.Popen(['python', 'think.py', "-i", command, "-v", Character, "-u", url], stderr=subprocess.STDOUT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True))
        time.sleep(0.01)
        self.pids[-1].stdin.write("\n")
        stdout_thread = threading.Thread(target=enqueue_output, args=(self.pids[-1].stdout, self.actual_queue))
        stdout_thread.daemon = True
        stdout_thread.start()
    def kill_pids(self):
        for pid in self.pids:
            try:
                if(pid.poll() is None):
                    os.kill(pid, signal.SIGTERM)
            except:
                pass
        self.pids = []
    def hear(self):
        if(not self.actual_queue.empty()):
            while (not self.actual_queue.empty()):
                self.queue += self.actual_queue.get()
         
        for pid in self.pids:
            if(not (pid.poll() is None)):
                self.pids.remove(pid)



l_pid = None
last_p = None
def SpeakText(command):
    global last_p
    global l_pid
    if(last_p and last_p.poll() == None): # make sure only 1 can run at a time.. cancel old ones if it gets to this point, if you want to queue do it before calling here somehow and check for last_p.poll() != None
        try:
            os.kill(l_pid, signal.SIGTERM)
        except:
            pass
    last_p = subprocess.Popen(['python', 'speak.py', '-i', command, '-v', 'Samantha'])
    l_pid = last_p.pid

spinner_index = 0
spinner_list = ["|","/","-","\\"]
def mic_listen(hearing_aid):
    global spinner_index
    global spinner_list
    print(spinner_list[spinner_index] ,end="\r"),
    spinner_index = spinner_index + 1
    if(spinner_index >= len(spinner_list)):
        spinner_index = 0
    time.sleep(1)
    hearing_aid.hear()
    global thinking
    thinking.hear()
    if( len(thinking.queue) > 0):
        SpeakText(thinking.queue)
        print(thinking.queue)
        thinking.queue = ""
    return hearing_aid.hearing_queue

def kill_it(histogram,hearing_aid):
    global l_pid
    global thinking    
    try:
        os.kill(l_pid, signal.SIGTERM)
    except:
        print("no process to kill")
    thinking.kill_pids()
    SpeakText("Confirmed.")
    

def listen_mode(histogram,hearing_aid):
    global kill_words;
    break_condition = True
    c = 0
    empty_timeout = ""
    while(break_condition):
        input = mic_listen(hearing_aid)
        for kill_word in kill_words:                    
            if(kill_word in input):
                kill_it(histogram,hearing_aid)
                raise Exception("Killed")
        print("Input: (" + input + ")"  +str(len(input)) + " " + str(len(histogram.current)))   
        if(c > 0):
            if(len(histogram.current) == 0 and len(input) == 0):
                break
            if(len(histogram.current) > 1 and histogram.current[-1] == "?" and len(input) == 0):
                break
            if(len(histogram.current) > 1 and histogram.current[-1] == "." and len(input) == 0):
                break
        histogram.add_to_string(input)
        c = c+1
        if(c > 10):
            break_condition = False

    print("You said: " + histogram.history)

    return histogram.history

def record_text(hearing_aid,histogram):
    global wake_word
    global kill_words
    while(1):
        try:
            histogram.add_to_string( mic_listen(hearing_aid) )
            if wake_word in histogram.history:
                killed = False
                for kill_word in kill_words:                    
                    if(kill_word in histogram.history):
                        killed = True
                        kill_it(histogram,hearing_aid)
                if(not killed):
                    try:
                        return listen_mode(histogram,hearing_aid)
                    except Exception as E:
                        print (E)
                        pass
            histogram.clear_if_needed(2)
        except sr.RequestError as e:
                print("Could not request results; {0}".format(e))
        except sr.UnknownValueError:
                print("unknown error occured")


history = []
print ("init histogram")
histogram = StringHistory()
print ("launch hearing")
aid = HearingAid()
aid.launch_hearing()
print ("launch thinking")
thinking = ThinkingAid()
while(1):
    histogram.clear_if_needed(0)
    print ("recording text")
    text = record_text(aid, histogram)
    histogram.clear_if_needed(0)
    
    print("create oobabooga request")
    new_message = {"role": "user", "content": text}
    history.append(new_message)
    try:
        thinking.launch(text)
        #response = send_to_oobabooga([new_message])
    except Exception as E:
        response = "Something went terribly wrong.\n "+str(e)
        print(response)
        
    
    #print ("speaking response")
    #SpeakText(response)
    #print(response)