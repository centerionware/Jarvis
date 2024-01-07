#!/usr/bin/env python

# This is a socketio client. 
import socketio
from socketio.exceptions import TimeoutError
import sys

config = sys.environ

from RequestHandlers import TextRequest, ImageRequest

class JarvisAgent:
    capabilities = []
    sio = None
    def __init__(self):
        self.sio = socketio.SimpleClient()
        self.callbacks()
        self.sio.connect('https://register.jarvis.ai.centerionware.com', transports=['websocket'])
        if( not "DISABLE_TEXT" in config):
            self.capabilities.append("TextRequest")
        if( not "DISABLE_IMAGE" in config):
            self.capabilities.append("ImageRequest")
        pass
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
        
    def call_backs(self):
        @self.sio.timeout(1)
        def heartbeat():
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

        @self.sio.event
        def connect():
            #self.sio.emit('subscribe','room')
            print('connection established')
            
        @self.sio.on("Capabilities")
        def capabilities(data):
            self.sio.emit("Capabilities", self.capabilities, room=request.sid)
            print(f"Data Received {data}")
        @self.sio.on("TextRequest")
        def text_request(data):
            print(f"Data Received {data}")

        @self.sio.on("ImageRequest")
        def image_request(data):
            print(f"Data Received {data}")
        @self.sio.event
        def auth(data):
            print(f"Data Received {data}")
        @self.sio.event
        def disconnect():
            print('disconnected from server')    
