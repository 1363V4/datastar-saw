import json
import asyncio
import logging
from uuid import uuid4
import string

from sanic import Sanic
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.sanic import datastar_response, read_signals

from tinydb import TinyDB
import redis.asyncio as redis

from views import main_view


app = Sanic(__name__)
app.static('/static/', './static/')
app.static('/', './index.html', name="index")
app.static('/cqrs', './cqrs.html', name="cqrs")

logging.basicConfig(filename='perso.log', encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)

# main_db = TinyDB("main_db.json", sort_keys=True, indent=2)
# words = main_db.table('words')
# users = main_db.table('users')
# temp_db = TinyDB("temp_db.json", sort_keys=True, indent=2)
# games = temp_db.table('games')
# deux db, une temp une importante?

@app.before_server_start
async def open_connections(app):
    app.ctx.db = {}
    app.ctx.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

@app.after_server_stop
async def close_connections(app):
    await app.ctx.redis_client.aclose()

@app.on_response
async def cookie(request, response):
    if not request.cookies.get("user_id"):
        user_id = uuid4().hex
        app.ctx.db[user_id] = ""
        response.add_cookie('user_id', user_id)

@app.post('/wotd') # cant handle spaces dumb design lol
@datastar_response
async def wotd(request):
    user_id = request.cookies.get('user_id')
    # html = await main_view()
    inputs = app.ctx.db.get(user_id)
    if not inputs:
        inputs = ""
    key = (await read_signals(request)).get('key')
    if not key:
        return
    key = key.lower()
    if key.lower() in string.ascii_lowercase:
        inputs += f"{key}"
    else:
        match key:
            case " ":
                inputs += " "
            case "backspace" if inputs:
                inputs = inputs[:-1]
            case _:
                pass

    app.ctx.db[user_id] = inputs
    html = f"<div id='test'>{inputs}</div>"
    return SSE.patch_elements(html)

@app.get('/cqrs_sse')
@datastar_response
async def cqrs_sse(request):
    user_id = request.cookies.get('user_id')
    pubsub = app.ctx.redis_client.pubsub()
    channel = f"word:{user_id}"
    await pubsub.subscribe(channel)
    accum = ""
    try:
        async for message in pubsub.listen():
            if message.get('type') == "message":
                logger.info(str(message))
                key = message.get('data')
                accum += key
                html = f"<div id='test'>{accum}</div>"
                yield SSE.patch_elements(html)
    except asyncio.CancelledError:
        raise
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()

@app.post('/cqrs_pit')
@datastar_response
async def cqrs_pit(request):
    logger.info(request.body)
    key = request.json.get('key')
    user_id = request.cookies.get('user_id')
    if not key:
        return
    key = key.lower()
    if key.lower() in string.ascii_lowercase:
        await app.ctx.redis_client.publish(f"word:{user_id}", key)


if __name__ == "__main__":
    app.run(
    debug=False,
    auto_reload=True,
    unix='saw.sock',
    access_log=False
    )
