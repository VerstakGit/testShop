from aiohttp import web
from handlers import couriers, update_couriers, orders, assign_orders, complete_orders, courier_info
import sqlite3


def create_application(path):
    app = web.Application()
    try:
        db = sqlite3.connect(path)
        app['db'] = db
    except sqlite3.Error as e:
        print(e)
    app.add_routes([web.post('/couriers', couriers),
                    web.patch('/couriers/{id}', update_couriers),
                    web.post('/orders', orders),
                    web.post('/orders/assign', assign_orders),
                    web.post('/orders/complete', complete_orders),
                    web.get('/couriers/{id}', courier_info)])
    return app


app = create_application("database.db")

if __name__ == '__main__':
    web.run_app(app)
