
import requests
import queue
import threading
import comfyui_api

class TextRequest:
    def threaded_query(TR_OBJ, args):
        id = TR_OBJ.id
        queue = TR_OBJ.queue
        remote_url = 'http://localhost:11434/api/generate'
        if(args["model"] == "llava"):
            new_args = {
                "model": args["model"],
                "stream": args["stream"],
                #Make a string out of all the messages roles and contents to fill the prompt
                "prompt": "",
                # fill in the images from the messages that have them
                "images": []
            }
            for message in args["messages"]:
                if(message["role"] != "assistant"):
                    content = message["content"]
                    if(content[0] == "$"): content = content[1:]
                    new_args["prompt"] +=  content + "\n"
                if("images" in message):
                    for image in message["images"]:
                        new_args["images"].append(image)
            output = requests.post(remote_url, json=new_args).content.decode('utf-8')
            print("Received output from llava: " + str(output))
            queue.put([id,output])
            return
        output = requests.post(remote_url.replace("generate", "chat"), json=args).content.decode('utf-8')
        print("received output from mistral")
        queue.put([id, output])

    def __init__(self, prompt):
        self.id = prompt[0]
        self.prompt = prompt[1]
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self.threaded_query, args=(self, self.prompt))
        pass
    def response(self):
        if(not self.queue.empty()):
                while (not self.queue.empty()):
                    return self.queue.get()
        return None
    def error(self, error):
        pass

class ImageRequest:
    def threaded_query(IR_OBJ, args):
        id = IR_OBJ.id
        queue = IR_OBJ.queue
        url = "localhost:8188"
        client = comfyui_api.Client(url)
        output = client.get_images(client.ws, args)
        queue.put([id,output])
        client.ws.close()
    def __init__(self, prompt):
        self.id = prompt[0]
        self.prompt = prompt[1]
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self.threaded_query, args=(self, self.prompt))
        pass
    def response(self):
        if(not self.queue.empty()):
                while (not self.queue.empty()):
                    return self.queue.get()
        return None
    def error(self, error):
        pass
