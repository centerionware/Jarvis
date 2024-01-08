#!/usr/bin/env python

# This is a socketio client. 
import socketio
from socketio.exceptions import TimeoutError
import os
import time

config = os.environ
sio = socketio.Client()
from RequestHandlers import TextRequest, ImageRequest
JA = None
class JarvisAgent:
    def __init__(self):
        global JA
        global sio
        JA = self
        self.capabilities = []
        self.sio = sio
        #self.sio = socketio.Client()
        self.callbacks()
        self.sio.connect('https://register.jarvis.ai.centerionware.com', transports=['websocket'])
        time.sleep(1)
        if( not hasattr(config, "DISABLE_TEXT")):
            self.capabilities.append("TextRequest")
        if( not hasattr(config, "DISABLE_IMAGE")):
            self.capabilities.append("ImageRequest")
        self.text_requests = []
        self.image_requests = []
    def image_launch(self, prompt):
        self.text_requests.append(TextRequest(prompt))
        pass
    def text_launch(self, prompt):
        self.image_requests.append(ImageRequest(prompt))
        pass
    def run(self):
        self.sio.wait()
    def heartbeat(self):
        for tr in self.text_requests:
            resp = tr.response()
            if(resp is not None):
                self.sio.emit("TextResponse", resp)
                self.text_requests.remove(tr)
        for ir in self.image_requests:
            resp = ir.response()
            if(resp is not None):
                self.sio.emit("ImageResponse", resp)
                self.image_requests.remove(ir)     
    def callbacks(self):
        pass

def heartbeat(v):
    global JA
    print(str(v))
    if(JA != None):
        JA.heartbeat(1)
    pass
sio.start_background_task(heartbeat,1)


@sio.on("Capabilities")
def capabilities():
    global JA
    JA.sio.emit("Capabilities", JA.capabilities)
    print("Sent Capabilities")

@sio.event
def connect():
    #self.sio.emit('subscribe','room')
    capabilities()
    print('connection established')

@sio.on("TextRequest")
def text_request(data):
    global JA
    JA.text_launch(data)
    print(f"Data Received {data}")

@sio.on("ImageRequest")
def image_request(data):
    global JA
    JA.image_launch(data)
    print(f"Data Received {data}")

@sio.event
def auth(data):
    print(f"Data Received {data}")
@sio.event
def disconnect():
    print('disconnected from server')    
