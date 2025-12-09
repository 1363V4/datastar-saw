import htpy as h


async def main_view(game_id=None):

    html = h.body(".gc.gf")[
        h.div(
            **{'data-signals:key':''},
            **{'data-on:keydown__window':"$key = evt; @post('/wotd')"}
        ),
        h.div("#lines")[

        ]
    ]
    return str(html)
