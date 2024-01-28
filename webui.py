# Original Source: https://stackoverflow.com/questions/53689602/python-3-websockets-server-http-server-run-forever-serve-forever
import aiohttp
from aiohttp import web, WSCloseCode
import asyncio
import nest_asyncio
class WebUI:
    def __init__(self, drawing, thinking, searching):
        self.search_handler = searching
        self.text_handler = thinking
        self.image_handler = drawing
        self.prompt_from_file = None
        with(open("/app/search_html_prompt.txt", "r")) as f:
            self.prompt_from_file = f.read()
        

    async def http_handler(self, request):
        fcont = ""
        with open("/app/webui.html", "r") as f:
            fcont = f.read()
        if(request.method == "POST"):
            pass
        return web.Response(text=fcont, content_type='text/html')

    async def css_handler(self, request):
        fcont = ""
        with open("/app/webui.css", "r") as f:
            fcont = f.read()
        return web.Response(text=fcont,content_type='text/css')

    async def js_handler(self, request):
        fcont = ""
        with open("/app/webui.js", "r") as f:
            fcont = f.read()
        return web.Response(text=fcont,content_type='text/javascript')

    async def search_websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    await ws.send_str("Searching...")
                    if(self.search_handler != None):
                        await self.search_handler.launch(msg.data, False, ws, msg.data, "auto")
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' % ws.exception())

        return ws

    def create_runner(self, ):
        app = web.Application()
        app.add_routes([
            web.get('/',   self.http_handler),
            web.get('/webui.css',   self.css_handler),
            web.get('/webui.js',   self.js_handler),
            web.get('/search',   self.http_handler),
            web.get('/ws', self.search_websocket_handler),
        ])
        return web.AppRunner(app)

    async def start_server(self, host="0.0.0.0", port=1337):
        runner = self.create_runner()
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

    async def startit(self, ):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start_server)
        return loop

if __name__ == "__main__":
    #startit().run_forever()
     n = WebUI()
     loop = asyncio.get_event_loop()
     loop.run_until_complete(n.start_server())
     loop.run_forever()