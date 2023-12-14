import requests
import speech_recognition as sr
import subprocess
import os
import signal
import time
import json
import argparse
import AppOpener

parser = argparse.ArgumentParser("python jarvis.py -i \"Hello World\" -v \"Jarvis\"")
parser.add_argument("-c", help="Oobabooga UI Character to use", type=str, default="Jarvis")
parser.add_argument("-v", help="Output voice to use", type=str, default="Samantha")
parser.add_argument("-w", help="Wake word", type=str, default="Jarvis")
parser.add_argument("-u", help="Url", type=str, default="http://127.0.0.1:5000/v1/chat/completions")
args = parser.parse_args()


r = sr.Recognizer()

wake_word = args.w

kill_words = ["shut up","nevermind","never mind","shut it","shut it down","shut down","shut it down"]

import signal
import sys

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    global thinking
    thinking.kill_pids()
    kill_it(None, None)
    global aid
    aid.__del__()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


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
    def __del__(self):
        print("Cleaning HearingAid")
        try:
            os.kill(self.hearing_pid.pid, signal.SIGTERM)
        except:
            pass
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
    def __del__(self):
        print("Cleaning ThinkingAid")
        self.kill_pids()
    def launch(self, command):
        global args
        
        self.command = command
        self.pids.append( subprocess.Popen(['python', 'think.py', "-i", command, "-v", args.c, "-u", args.u], stderr=subprocess.STDOUT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True))
        time.sleep(0.01)
        self.pids[-1].stdin.write("\n")
        stdout_thread = threading.Thread(target=enqueue_output, args=(self.pids[-1].stdout, self.actual_queue))
        stdout_thread.daemon = True
        stdout_thread.start()
    def kill_pids(self):
        for pid in self.pids:
            try:
                if(pid.poll() is None):
                    os.kill(pid.pid, signal.SIGTERM)
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


class AppAid():
    def __init__(self):
        self.apps = AppOpener.give_appnames()
    def try_open_app(self, app_name):
        #if(app_name.lower() in self.apps):
        AppOpener.open(app_name, match_closest = True)
        
        

l_pid = None
last_p = None


def SpeakText(command):
    global last_p
    global l_pid
    global args
    if(last_p and last_p.poll() == None): # make sure only 1 can run at a time.. cancel old ones if it gets to this point, if you want to queue do it before calling here somehow and check for last_p.poll() != None
        try:
            os.kill(l_pid, signal.SIGTERM)
        except:
            pass
    last_p = subprocess.Popen(['python', 'speak.py', '-i', command, '-v', args.v])
    l_pid = last_p.pid

class RetryHandler():
    def __init__(self):
        self.retryAid = []
        return
    def clear_retries(self):
        self.retryAid = []
    def try_retry(self,prompt,error):
        found = False
        for i in self.retryAid:
            if(i[0] in prompt):
                found = True
                if(i[1] > 3):
                    #abort
                    print("Aborting retries on query")
                    SpeakText("Aborting retries on query")
                else:
                    i[1] = i[1] + 1
                    self.send_out(prompt, error)
        if( not found ):
            self.retryAid.append([prompt,1])
            self.send_out(prompt, error)
    def remove_from_retry(self, prompt):
        for i in self.retryAid:
            if(i[0] in prompt):
                self.retryAid.remove(i)
                return
    def send_out(self, prompt, error):
        print ("Retryifying")
        global thinking
        thinking.launch(prompt + " produced the error (" + error + ")\nplease try again.")

Retryifier = RetryHandler()
import webbrowser
def action_handler(action):
    if "browser-launch" in action:
        try:
            url = action.split(" ")[1]
            webbrowser.open(url, new=0, autoraise=True)
        except Exception as E:
            webbrowser.open("", new=0, autoraise=True)
    if "open-app" in action:
        app_name = ""
        try:
           app_name = action.split(" ")[1]
        except:
           pass
        AppOpener.open(app_name, match_closest = True)
    
def ParseResponse(response):
    response = json.loads(response)
    voice_output = "Jarvis"
    try:
        final_response = json.loads(response["response"])
        if("characterName" in final_response):
            voice_output = final_response["characterName"]
        if("response" in final_response):
            if("speech" in final_response["response"]):
                SpeakText(final_response["response"]["speech"])
                print("Speaking: " + final_response["response"]["speech"])
            if("action" in final_response["response"]):
                action = final_response["response"]["action"]
                action_handler(action)
                print(action)
        Retryifier.remove_from_retry(response['prompt'])
    except Exception as E:
        Retryifier.try_retry(response['prompt'], str(E))
        print ("exception parsing response: " + str(E))

spinner_index = 0
spinner_list = ["|","/","-","\\"]
def mic_listen(hearing_aid, spinamnt):
    global spinner_index
    global spinner_list
    print(spinner_list[spinner_index] ,end="\r"),
    spinner_index = spinner_index + spinamnt
    if(spinner_index >= len(spinner_list)):
        spinner_index = 0
    if(spinner_index < 0):
        spinner_index = len(spinner_list)-1
    time.sleep(1)
    hearing_aid.hear()
    global thinking
    thinking.hear()
    if( len(thinking.queue) > 0):
        print("Heard back from the AI Chatbot: " + thinking.queue)
        ParseResponse(thinking.queue)
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

class p_watcher():
    def __del__(self):
        print("Cleaning remaining Speaker if any")
        kill_it(None, None)
p_watcher_instance = p_watcher()


def listen_mode(histogram,hearing_aid):
    global kill_words;
    break_condition = True
    c = 0
    empty_timeout = ""
    while(break_condition):
        input = mic_listen(hearing_aid, -1)
        for kill_word in kill_words:                    
            if(kill_word in input.lower()):
                kill_it(histogram,hearing_aid)
                raise Exception("Killed " + kill_word)
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
            histogram.add_to_string( mic_listen(hearing_aid,1) )
            if wake_word.lower() in histogram.history.lower():
                killed = False
                print("Awakening to " + histogram.history)
                for kill_word in kill_words:                    
                    if(kill_word in histogram.history.lower()):
                        killed = True
                        kill_it(histogram,hearing_aid)
                        print("Killed " + kill_word)
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