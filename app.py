import json
import asyncio
import logging
from uuid import uuid4
import string
import queue

from sanic import Sanic
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py import attribute_generator as data
from datastar_py.sanic import datastar_response, read_signals

from tinydb import TinyDB
import redis.asyncio as redis

import htpy as h


app = Sanic(__name__)
app.static('/static/', './static/')
app.static('/', './index.html', name="index")

logging.basicConfig(filename='perso.log', encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)

# main_db = TinyDB("main_db.json", sort_keys=True, indent=2)
# words = main_db.table('words')
# users = main_db.table('users')
# temp_db = TinyDB("temp_db.json", sort_keys=True, indent=2)
# games = temp_db.table('games')
# deux db, une temp une importante?

async def wassup_psutil():
    while True:
        ... # pour q les reads

# app.add_task(wassup_psutil)

@app.before_server_start
async def open_connections(app):
    app.ctx.db = {}
    app.ctx.write_q = queue.Queue()
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

# UTILS

async def process_key(key, lines):
    ...


# VIEWS

async def main_view(game_id=None):
    lines = ("MOTUS", "AC___")
    html = h.body(".gc.gf")[
        h.div(
            data.signals({'key': 'ok'}),
            data.on('keydown', "$key = evt.key; @post('/wotd')").window
        ),
        h.div("#lines")[
            (h.div(".line")[line] for line in lines)
        ]
    ]
    return str(html)

# ROUTES

@app.get('/wotd')
@datastar_response
async def wotd(request):
    user_id = request.cookies.get('user_id')
    game_id = uuid4().hex
    app.ctx.db['user_id'] = game_id
    pubsub = app.ctx.redis_client.pubsub()
    channel = f"game:{game_id}"
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            html = await main_view()
            yield SSE.patch_elements(html)
    except asyncio.CancelledError:
        raise
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()

@app.post('/wotd')
@datastar_response
async def cqrs_pit(request):
    key = request.json.get('key')
    if not key:
        return
    user_id = request.cookies.get('user_id')
    game_id = app.ctx.db.get('user_id')
    if not game_id:
        return
    key = key.lower()
    if key not in string.ascii_lowercase:
        return
    await app.ctx.redis_client.publish(f"game:{game_id}", key)


if __name__ == "__main__":
    app.run(
    debug=False,
    auto_reload=True,
    unix='saw.sock',
    access_log=False
    )
