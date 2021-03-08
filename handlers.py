from aiohttp import web
from courier import Courier
from courier import get_courier
from order import Order
from order import get_order


salary = {"foot": 2, "bike": 5, "car": 9}


async def courier_info(request):
    courier_id = request.match_info.get('id')
    courier = get_courier(courier_id, request.app['db'])
    if courier is None:
        return web.Response(status=400)
    sum_salary = courier.delivery_count * 500 * salary[courier.type]
    min_time = courier.get_min_average_delivery_time(request.app['db'])
    if min_time is None:
        rating = 0
    else:
        rating = (60*60 - min(min_time, 60*60))/(60*60)*5
    return web.json_response(status=200, data={"courier_id": courier.id, "courier_type": courier.type,
                                               "regions": courier.regions, "working_hours": courier.working_hours,
                                               "rating": rating, "earnings": sum_salary})


async def complete_orders(request):
    json = await request.json()
    courier_id = 0
    order_id = 0
    for k, v in json.items():
        if k == "courier_id" and type(v) is int and v > 0:
            courier_id = v
        elif k == "order_id" and type(v) is int and v > 0:
            order_id = v
        else:
            return web.Response(status=400)
    if courier_id == 0 or order_id == 0:
        return web.Response(status=400)
    order = get_order(order_id, request.app['db'])
    if order is None or order.courier_id != courier_id:
        return web.Response(status=400)
    if order.complete == 0:
        order.set_complete(request.app['db'])
    return web.json_response(status=200, data={"order_id": order.id})


async def assign_orders(request):
    json = await request.json()
    cur_orders = []
    for k, v in json.items():
        if k == "courier_id" and type(v) is int and v > 0:
            courier = get_courier(v, request.app['db'])
            if courier is None:
                return web.Response(status=400)
            else:
                cur_orders = courier.get_compatible_orders(request.app['db'])
                for order in cur_orders:
                    order.set_courier(request.app['db'], courier.id)
                courier.increase_delivery_count(request.app['db'])
        else:
            return web.Response(status=400)
    return web.json_response(status=200, data={"orders": [{"id": order.id} for order in cur_orders]})


async def orders(request):
    json = await request.json()
    incorrect_objects = []
    objects = []
    for k, v in json.items():
        if k == "data":
            for obj in v:
                order = Order(obj.get("order_id"), obj.get("weight"), obj.get("region"), obj.get("delivery_hours"), None, 0)
                incorrect = False
                for key, val in obj.items():
                    if key == "order_id" and type(val) is int and val > 0:
                        order.id = val
                    elif key == "weight" and (type(val) is float or type(val) is int) and 0.01 <= val <= 50:
                        order.weight = val
                    elif key == "region" and type(val) is int and val > 0:
                        order.region = val
                    elif key == "delivery_hours" and type(val) is list and all(type(x) is str for x in val):
                        order.delivery_hours = val
                    else:
                        incorrect = True
                if incorrect or order.region is None or order.delivery_hours is None or order.weight is None:
                    incorrect_objects.append({"id": order.id})
                else:
                    objects.append({"id": order.id})
                    order.save(request.app['db'])
        else:
            return web.Response(status=400)
    if len(incorrect_objects) > 0:
        return web.json_response(status=400, data={"validation_error": {"orders": incorrect_objects}})
    else:
        return web.json_response(status=201, data={"orders": objects})


async def update_couriers(request):
    json = await request.json()
    id = request.match_info.get('id')
    incorrect = False
    courier = Courier(id, None, None, None, 0)
    for key, val in json.items():
        if key == "courier_type" and type(val) is str and val in ('foot', 'bike', 'car'):
            courier.type = val
        elif key == "regions" and type(val) is list and all(type(x) is int and x > 0 for x in val):
            courier.regions = val
        elif key == "working_hours" and type(val) is list and all(type(x) is str for x in val) and len(val) <= 3:
            courier.working_hours = val
        else:
            incorrect = True
    if incorrect:
        return web.Response(status=400)
    courier = courier.update(request.app['db'])
    orders = courier.get_incompatible_orders(request.app['db'])
    for order in orders:
        order.remove_courier(request.app['db'])
    return web.json_response(status=200, data={"courier_id": courier.id, "courier_type": courier.type,
                                               "regions": courier.regions, "working_hours": courier.working_hours})


async def couriers(request):
    json = await request.json()
    objects = []
    incorrect_objects = []
    for k, v in json.items():
        if k == "data":
            for obj in v:
                courier = Courier(obj.get("courier_id"), obj.get("courier_type"), obj.get("regions"), obj.get("working_hours"), 0)
                incorrect = False
                for key, val in obj.items():
                    if key == "courier_id" and type(val) is int and val > 0:
                        courier.id = val
                    elif key == "courier_type" and type(val) is str and val in ('foot', 'bike', 'car'):
                        courier.type = val
                    elif key == "regions" and type(val) is list and all(type(x) is int and x > 0 for x in val):
                        courier.regions = val
                    elif key == "working_hours" and type(val) is list and all(type(x) is str for x in val) and len(val) <= 3:
                        courier.working_hours = val
                    else:
                        incorrect = True
                if incorrect or courier.regions is None or courier.working_hours is None or courier.type is None:
                    incorrect_objects.append({"id": courier.id})
                else:
                    objects.append({"id": courier.id})
                    courier.save(request.app['db'])
        else:
            return web.Response(status=400)

    if len(incorrect_objects) > 0:
        return web.json_response(status=400, data={"validation_error": {"couriers": incorrect_objects}})
    else:
        return web.json_response(status=201, data={"couriers": objects})
