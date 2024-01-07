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

from flask import Flask, jsonify, request, abort, g as _g
import config
from flask_socketio import SocketIO, join_room, leave_room, emit
import threading
# run the flask app in a thread
import os

#import drawing_aid 
#import thinking_aid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecret!'
socketio = SocketIO(app)
import queue
import uuid
# This is a dictionary of agents that are registered with the controller
class JarvisMC:
    image_agents = []
    text_agents = []
    drawing = None
    thinking = None
    server_thread = None
    def __init__(self, v_drawing_aid, v_thinking_aid):
        self.drawing = v_drawing_aid
        self.thinking = v_thinking_aid
        pass
    # Function to create websocket connection
    @socketio.on('capabilities')
    def handle_my_custom_event(self, json):
        print('received json: ' + str(json))
        client_id = request.sid
        print('client_id: ' + str(client_id))

        for cap in json["capabilities"]:
            if(cap == "ImageRequest"):
                self.image_agents.append([client_id, json, queue.Queue()])
            elif(cap == "TextRequest"):
                self.text_agents.append([client_id, json, queue.Queue()])

    # Add the following route to handle agent connection/disconnection
    @socketio.on('connect')
    def on_agent_connect(self, client_id):
        emit("Capabilities", room=request.sid)
        print('Agent connected, requested capabilities!')

    @socketio.on('disconnect')
    def on_agent_disconnect(self):
        client_id = request.sid
        for agent in self.image_agents:
            if(agent[0] == client_id):
                self.image_agents.remove(agent)
        for agent in self.text_agents:
            if(agent[0] == client_id):
                self.text_agents.remove(agent)
        print('Agent disconnected!')
    def get_text_agent(self):
        smallest_queue = None
        for agent in self.text_agents:
            if(smallest_queue is None):
                smallest_queue = agent
            elif(smallest_queue[2].qsize() > agent[2].qsize()):
                smallest_queue = agent
        return smallest_queue
    def get_image_agent(self):
        smallest_queue = None
        for agent in self.image_agents:
            if(smallest_queue is None):
                smallest_queue = agent
            elif(smallest_queue[2].qsize() > agent[2].qsize()):
                smallest_queue = agent
        return smallest_queue
    @socketio.on('image response')
    def image_response(self, json):
        agent_id = request.sid
        for agent in self.image_agents:
            if(agent[0] == agent_id):
                print("Received image response from agent: " + str(agent_id))
                queue = agent[2].get()
                self.drawing.queue.put([json, queue[2]])
                # Response is now available with the jarvis discord interaction object here so can add a response back to drawing_aid
        pass
    def image_request(self, interaction, json_prompt):
        available_agent = self.get_image_agent()
        if(available_agent is None):
            print("No image agents available")
            raise Exception("No image agents available")
        id = str(uuid.uuid4())
        available_agent[2].put([id, json_prompt, interaction])
        emit("ImageRequest", {"id":id,"prompt":json_prompt}, room=available_agent[0])
    @socketio.on('text response')
    def text_response(self, json):
        agent_id = request.sid
        for agent in self.text_agents:
            if(agent[0] == agent_id):
                print("Received text response from agent: " + str(agent_id))
                queue = agent[2].get()
                self.thinking.queue.put([json, queue[2]])
                # Response is now available with the jarvis discord interaction object here so can add a response back to thinking_aid
        pass
    def text_request(self, interaction, json_prompt):
        available_agent = self.get_text_agent()
        if(available_agent is None):
            print("No text agents available")
            raise Exception("No text agents available")
        id = str(uuid.uuid4())
        available_agent[2].put([id, json_prompt, interaction])
        emit("TextRequest", {"id":id,"prompt":json_prompt}, room=available_agent[0])
    def start(self):
        config = os.environ
        if(config.MC_HOST is None):
            config.MC_HOST = "*"
        if(config.MC_PORT is None):
            config.MC_PORT = 5000
        self.server_thread = threading.Thread(target=socketio.run, args=(app, config.MC_HOST, config.MC_PORT))
        pass
    def stop(self):
        if(self.server_thread is not None):
            socketio.stop()
            self.server_thread.join()
            self.server_thread = None

