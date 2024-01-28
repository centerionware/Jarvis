# Original Source: https://stackoverflow.com/questions/53689602/python-3-websockets-server-http-server-run-forever-serve-forever
import aiohttp
from aiohttp import web, WSCloseCode
import asyncio
import nest_asyncio

async def http_handler(request):
    fcont = ""
    with open("/app/webui.html", "r") as f:
        fcont = f.read()
    if(request.method == "POST"):
        pass
    return web.Response(text=fcont, content_type='text/html')

async def css_handler(request):
    fcont = ""
    with open("/app/webui.css", "r") as f:
        fcont = f.read()
    return web.Response(text=fcont,content_type='text/css')

async def js_handler(request):
    fcont = ""
    with open("/app/webui.js", "r") as f:
        fcont = f.read()
    return web.Response(text=fcont,content_type='text/javascript')

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str('some websocket message payload')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())

    return ws

def create_runner():
    app = web.Application()
    app.add_routes([
        web.get('/',   http_handler),
        web.get('/webui.css',   css_handler),
        web.get('/webui.js',   js_handler),
        web.get('/search',   http_handler),
        web.get('/ws', websocket_handler),
    ])
    return web.AppRunner(app)

async def start_server(host="0.0.0.0", port=1337):
    runner = create_runner()
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

async def startit():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    return loop

if __name__ == "__main__":
    #startit().run_forever()
     loop = asyncio.get_event_loop()
     loop.run_until_complete(start_server())
     loop.run_forever()