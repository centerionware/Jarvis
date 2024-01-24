#!/usr/bin/env python

import os
import time
import json
import asyncio
import websockets
from RequestHandlers import TextRequest, ImageRequest, SearchRequest
import traceback
import base64

config = os.environ
JA = None

class JarvisAgent:
    def __init__(self):
        global JA
        JA = self
        self.capabilities = []
        self.websocket = None
        if( config.get("DISABLE_TEXT", "") == ""):
            self.capabilities.append("TextRequest")
        if( config.get("DISABLE_IMAGE","") == ""):
            self.capabilities.append("ImageRequest")
        if( config.get("DISABLE_SEARCH","") == ""):
            if os.path.exists('/var/run/docker.sock'):
                self.capabilities.append("WebSearch")
        self.text_requests = []
        self.image_requests = []
        self.search_requests = []
    async def run(self):
        backoff = 1
        while(True):
            await asyncio.sleep(backoff)
            try:
                async with websockets.connect("wss://register.jarvis.ai.centerionware.com") as websocket:
                    print ("Connected")
                    self.websocket = websocket
                    await websocket.send(json.dumps({"type": "Capabilities", "payload": {"capabilities": self.capabilities}}))
                    print ("Sent capabilities: " + str(self.capabilities))
                    while True:
                        try:
                            message = await websocket.recv()
                            print("message received." + message)
                            pkt = json.loads(message)
                            if(pkt["type"] == "ImageRequest"):
                                self.image_requests.append(ImageRequest(pkt["payload"]))
                            if(pkt["type"] == "TextRequest"):
                                self.text_requests.append(TextRequest(pkt["payload"]))
                            if(pkt["type"] == "SearchRequest"):
                                self.search_requests.append(SearchRequest(pkt["payload"]))
                            if(pkt["type"] == "Capabilities"):
                                await websocket.send(json.dumps({"type": "Capabilities", "payload": {"capabilities": self.capabilities}}))
                        except Exception as E:
                            traceback.print_exc()
                            print("Error:" + str(E) )
                            break
            except Exception as E:
                traceback.print_exc()
                print("Exception:" + str(E))
            if(backoff < 10):
                backoff = backoff*2
            print("Reconnecting...")
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
                # for e in resp:
                #     for img in resp[e]:
                #         resp[e][img] = base64.b64encode(resp[e][img]).decode('utf-8')
                await self.websocket.send(json.dumps({"type": "ImageResponse", "payload": resp}))
                #self.sio.emit("ImageResponse", resp)
                self.image_requests.remove(ir)
        for sr in self.search_requests:
            resp = sr.response()
            if(resp is not None):
                await self.websocket.send(json.dumps({"type": "SearchResponse", "payload": resp}))
                self.search_requests.remove(sr)
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