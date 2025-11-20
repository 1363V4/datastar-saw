import htpy as h

async def main_view(game_id=None):
    html = h.body(".gc.gf")[
        h.main["hello"]
    ]
    return str(html)
