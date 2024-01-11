#!/usr/bin/env python

import os
import time
import json
import asyncio
import websockets
from RequestHandlers import TextRequest, ImageRequest

config = os.environ
JA = None

class JarvisAgent:
    def __init__(self):
        global JA
        JA = self
        self.capabilities = []
        self.websocket = None
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
    async def run(self):
        async with websockets.connect("wss://register.jarvis.ai.centerionware.com") as websocket:
            self.websocket = websocket
            await websocket.send(json.dumps({"type": "Capabilities", "payload": {"capabilities": self.capabilities}}))
            while True:
                try:
                    message = await websocket.recv()
                    pkt = json.loads(message)
                    if(pkt["type"] == "ImageRequest"):
                        self.image_launch(pkt["payload"], websocket)
                    if(pkt["type"] == "TextRequest"):
                        self.text_launch(pkt["payload"], websocket)
                    if(pkt["type"] == "Capabilities"):
                        await websocket.send(json.dumps({"type": "Capabilities", "payload": {"capabilities": self.capabilities}}))
                except:
                    print("Error")
                    break
    async def heartbeat(self):
        await asyncio.sleep(1)
        for tr in self.text_requests:
            resp = tr.response()
            if(resp is not None):
                await self.websocket.send(json.dumps({"type": "TextResponse", "payload": resp}))
                self.text_requests.remove(tr)
        for ir in self.image_requests:
            resp = ir.response()
            if(resp is not None):
                await self.websocket.send(json.dumps({"type": "ImageResponse", "payload": resp}))
                #self.sio.emit("ImageResponse", resp)
                self.image_requests.remove(ir)
        asyncio.create_task(self.heartbeat())
    def callbacks(self):
        pass

async def main():
    global JA
    JA = JarvisAgent()
    await JA.heartbeat()
    await JA.run()
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())