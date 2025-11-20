# import asyncio

from sanic import Sanic
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.sanic import datastar_response

from tinydb import TinyDB

from views import main_view


app = Sanic(__name__)
app.static('/static/', './static/')
app.static('/', './index.html', name="index")

main_db = TinyDB("main_db.json", sort_keys=True, indent=2)
words = main_db.table('words')
users = main_db.table('users')
temp_db = TinyDB("temp_db.json", sort_keys=True, indent=2)
games = temp_db.table('games')
# deux db, une temp une importante?


@app.get('/wotd')
@datastar_response
async def wotd(request):
    html = await main_view()
    return SSE.patch_elements(html)

if __name__ == "__main__":
    app.run(debug=True, auto_reload=True, access_log=False)
