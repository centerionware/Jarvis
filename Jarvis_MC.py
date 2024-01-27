#!python3

# The idea here is to create a main controller for registration of agents that run the ollama and or comfyui

# It will provide a websocket  endpoint where agents can register back to jarvis to be used for inference.

# It should perform tests to calculate load time and loaded run times for the available endpoints
# Consistantly update these datapoints
# Provide a function that can return an available endpoint, maybe it should be a full proxy.. try and keep one connection
# open to the agents, and proxy the requests through. This will reduce tcp overhead and allow scaleout to however many sockets the
# mc host can handle of agents.
# When a connection fails the agent is in charge of reconnecting, not the controller. No exponential backoff in the controller.


# Let's use flask and socketio

# from flask import Flask, jsonify, request, abort, g as _g

# from flask_socketio import SocketIO, join_room, leave_room, emit
import threading
# run the flask app in a thread
import os


import nest_asyncio
nest_asyncio.apply()

#import drawing_aid
#import thinking_aid

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'supersecret!'
# socketio = SocketIO(app,cors_allowed_origins="*")
import queue
import uuid
# @app.route("/")
# def is_running():
#     return 'running'
remote_servers = []
import base64
import asyncio
from websockets.server import serve
import json
import websockets
def dc_client(websocket):
    global MC
    MC.on_agent_disconnect(websocket)
    for server in remote_servers:
        if(server["socket"] == websocket):
            remote_servers.remove(server)
            return
    

async def handler(websocket):
    global MC
    while True:
        print ("Handling remote connection..")
        remote_servers.append({"socket": websocket, "capabilities": []})
        try:
            message = await websocket.recv()
        except websockets.ConnectionClosedOK:
            print("Client disconnected...")
            dc_client(websocket)
            print("Unable to remove server from remote_servers...")
            break
        except Exception as E:
            dc_client(websocket)
            print ("Generic Error: ", E)
            break
        pkt = json.loads(message)
        if(pkt["type"] == "Capabilities"):
            MC.handle_capabilities(pkt["payload"], websocket)
        if(pkt["type"] == "ImageResponse"):
            await MC.image_response(pkt["payload"], websocket)
        if(pkt["type"] == "TextResponse"):
            await MC.text_response(pkt["payload"], websocket)
        if(pkt["type"] == "SearchResponse"):
            await MC.search_response(pkt["payload"], websocket)

serv_instance = None
async def main(host, port):
    global serv_instance
    async with websockets.server.serve(handler, host, port, max_size=104857600) as SERVER_INSTANCE:
        if(serv_instance is None):
            serv_instance = SERVER_INSTANCE
        await asyncio.Future()  # run forever

def startit(host, port):
    asyncio.run(main(host, port))


MC = None
# This is a dictionary of agents that are registered with the controller
class JarvisMC:
    def __init__(self, v_drawing_aid, v_thinking_aid, v_searching_aid):
        self.image_agents = []
        self.text_agents = []
        self.search_agents = []
        self.server_thread = None
        self.drawing = v_drawing_aid
        self.thinking = v_thinking_aid
        self.searching = v_searching_aid
        self.send_queue = queue.Queue()
        global MC
        MC = self
        pass
    # Function to create websocket connection
    def handle_capabilities(self, json, websocket):
        print('received json: ' + str(json))
        client_id = websocket
        print('client_id: ' + str(client_id))

        for cap in json["capabilities"]:
            if(cap == "ImageRequest"):
                self.image_agents.append([client_id, json, queue.Queue()])
            elif(cap == "TextRequest"):
                self.text_agents.append([client_id, json, queue.Queue()])
            elif(cap == "SearchRequest"):
                self.search_agents.append([client_id, json, queue.Queue()])
    # Add the following route to handle agent connection/disconnection
    def on_agent_connect(self):
        print('Agent connected, requested capabilities!')

    def on_agent_disconnect(self, websocket):
        client_id = websocket
        for agent in self.image_agents:
            if(agent[0] == client_id):
                self.image_agents.remove(agent)
        for agent in self.text_agents:
            if(agent[0] == client_id):
                self.text_agents.remove(agent)
        for agent in self.search_agents:
            if(agent[0] == client_id):
                self.search_agents.remove(agent)
        print('Agent disconnected!')

    async def queuer(self, agent_id, json_prompt, interaction, output_type ):
        id = str(uuid.uuid4())
        output = json.dumps({"type": output_type, "payload": {"id":id,"prompt":json_prompt}})
        for agent in self.image_agents:
            if(agent[0] == agent_id[0]):
                if(agent[2].qsize() > 0):
                    self.send_queue.put([agent_id, output])
                    agent_id[2].put([id, json_prompt, interaction])
                    return True
        for agent in self.text_agents:
            if(agent[0] == agent_id[0]):
                if(agent[2].qsize() > 0):
                    self.send_queue.put([agent_id, output])
                    agent_id[2].put([id, json_prompt, interaction])
                    return True
        
        agent_id[2].put([id, json_prompt, interaction])
        await agent_id[0].send(output)
        return False
    async def queue_pusher(self):
        if( not self.send_queue.empty() ):
            next_item = self.send_queue.get()
            await next_item[0][0].send(next_item[1])

    async def handle_response(self, json, websocket, agents_list, output_item):
        agent_id = websocket
        for agent in agents_list:
            if(agent[0] == agent_id):
                print("Received image response from agent. " ) #+ str(agent_id))
                queue = agent[2].get()
                retry_count = 0
                while(json[0] != queue[0]):
                    print("Response id does not match request id. Requeue.")
                    agent[2].put(queue)
                    queue = agent[2].get()
                    if(retry_count >= queue.qsize()):
                        print("Can't find interaction in queue. Dropping response.")
                        await self.queue_pusher()
                        return
                    retry_count += 1
                output_item.queue.append([json[1], queue[2]])
                # Response is now available with the jarvis discord interaction object here so can add a response back to drawing_aid
        await self.queue_pusher()
        pass
    async def image_response(self, json, websocket):
        await self.handle_response(json, websocket, self.image_agents, self.drawing)
        pass
    async def search_response(self, json, websocket):
        await self.handle_response(json, websocket, self.search_agents, self.searching)
        pass
    async def text_response(self, json, websocket):
        await self.handle_response(json, websocket, self.text_agents, self.thinking)
        pass
    def get_image_agent(self):
        smallest_queue = None
        for agent in self.image_agents:
            if(smallest_queue is None):
                smallest_queue = agent
            elif(smallest_queue[2].qsize() > agent[2].qsize()):
                smallest_queue = agent
        return smallest_queue
    def get_text_agent(self):
        smallest_queue = None
        for agent in self.text_agents:
            if(smallest_queue is None):
                smallest_queue = agent
            elif(smallest_queue[2].qsize() > agent[2].qsize()):
                smallest_queue = agent
        return smallest_queue
    async def text_request(self, interaction, json_prompt):
        available_agent = self.get_text_agent()
        if(available_agent is None):
            print("No text agents available")
            raise Exception("No text agents available")
        print("Starting a text request")
        id = str(uuid.uuid4())
        await self.queuer(available_agent, json_prompt, interaction, "TextRequest")
        # available_agent[2].put([id, json_prompt, interaction])

        # await available_agent[0].send(json.dumps({"type": "TextRequest", "payload": {"id":id,"prompt":json_prompt}}))
    def get_search_agent(self):
        smallest_queue = None
        for agent in self.search_agents:
            if(smallest_queue is None):
                smallest_queue = agent
            elif(smallest_queue[2].qsize() > agent[2].qsize()):
                smallest_queue = agent
        return smallest_queue
    async def search_request(self, interaction, json_prompt):
        available_agent = self.get_search_agent()
        if(available_agent is None):
            print("No text agents available")
            raise Exception("No text agents available")
        print("Starting a text request")
        id = str(uuid.uuid4())
        available_agent[2].put([id, json_prompt, interaction])
        await available_agent[0].send(json.dumps({"type": "SearchRequest", "payload": {"id":id,"prompt":json_prompt}}))
    async def image_request(self, interaction, json_prompt):
        available_agent = self.get_image_agent()
        if(available_agent is None):
            print("No image agents available")
            raise Exception("No image agents available")
        print ("Starting an image request")
        await self.queuer(available_agent, json_prompt, interaction, "ImageRequest")
        # available_agent[2].put([id, json_prompt, interaction])
        # await available_agent[0].send(json.dumps({"type": "ImageRequest", "payload": {"id":id,"prompt":json_prompt}}))
    async def text_request(self, interaction, json_prompt):
        available_agent = self.get_text_agent()
        if(available_agent is None):
            print("No text agents available")
            raise Exception("No text agents available")
        print("Starting a text request")
        id = str(uuid.uuid4())
        available_agent[2].put([id, json_prompt, interaction])
        await available_agent[0].send(json.dumps({"type": "TextRequest", "payload": {"id":id,"prompt":json_prompt}}))
            # await available_agent[0].send(json.dumps({"type": "TextRequest", "payload": {"id":id,"prompt":json_prompt}}))
    async def start_async(self):
        config = os.environ
        host = "0.0.0.0"
        port = 5000
        if hasattr(config, 'MC_HOST'):
            host = config.MC_HOST
        if hasattr(config, 'MC_PORT'):
            port = config.MC_PORT
        print ("Starting MC server")
        await startit(host, port)
        print ("MC Server started")
    def start(self):
        config = os.environ
        host = "0.0.0.0"
        port = 5000
        if hasattr(config, 'MC_HOST'):
            host = config.MC_HOST
        if hasattr(config, 'MC_PORT'):
            port = config.MC_PORT
        self.server_thread = threading.Thread(target=startit, args=(host, port))
        self.server_thread.daemon = True
        self.server_thread.start()
        pass
    def stop(self):
        if(self.server_thread is not None):
            serv_instance.stop()
            self.server_thread.join()
            self.server_thread = None 