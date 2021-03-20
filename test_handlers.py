from main import create_application
import datetime
import time


def reset_db(db):
    cur = db.cursor()
    cur.execute('DELETE FROM couriers')
    cur.execute('DELETE FROM orders')
    db.commit()


async def test_courier(aiohttp_client, loop):
    app = create_application("test_database.db")
    reset_db(app['db'])
    client = await aiohttp_client(app)

    resp = await client.post('/couriers', json={"empty": "fake"})
    assert resp.status == 400
    text = await resp.text()
    assert text == ''

    tests = [
        {
            "body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]},
                         {"courier_id": 2, "type": "unknown"}]},
            "status": 400,
            "result": {"validation_error": {"couriers": [{"id": 2}]}}
        },
        {
            "body": {
                "data": [{"courier_id": 1, "courier_type": "unknown", "regions": [1], "working_hours": ["11:00-18:00"]},
                         {"courier_id": 2, "regions": "2", "courier_type": "bike", "working_hours": ["9:00-10:00"]}]},
            "status": 400,
            "result": {"validation_error": {"couriers": [{"id": 1}, {"id": 2}]}},
        },
        {
            "body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]},
                         {"courier_id": 2, "courier_type": "car", "regions": [1, 2, 3, 4],
                          "working_hours": ["9:00-15:00", "18:00-21:00"]}]},
            "status": 201,
            "result": {"couriers": [{"id": 1}, {"id": 2}]}
        }
    ]

    for test in tests:
        resp = await client.post('/couriers', json=test["body"])
        assert resp.status == test["status"]
        json = await resp.json()
        assert json == test["result"]


async def test_update_couriers(aiohttp_client, loop):
    app = create_application("test_database.db")
    reset_db(app['db'])
    client = await aiohttp_client(app)
    tests = [
        {
            "create_body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]}]},
            "create_status": 201,
            "courier_id": 1,
            "update_body": {"regions": [1, 2, 3, 4]},
            "update_status": 200,
            "result": {"courier_id": 1, "courier_type": "foot", "regions": [1, 2, 3, 4],
                       "working_hours": ["11:00-18:00"]}
        },
        {
            "create_body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]}]},
            "create_status": 201,
            "courier_id": 1,
            "update_body": {"regions": "f"},
            "update_status": 400,
        },
        {
            "create_body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]}]},
            "create_status": 201,
            "courier_id": 1,
            "update_body": {"courier_type": "bike", "working_hours": ["9:00-21:00"]},
            "update_status": 200,
            "result": {"courier_id": 1, "courier_type": "bike", "regions": [1],
                       "working_hours": ["9:00-21:00"]}
        },
    ]

    for test in tests:
        resp = await client.post('/couriers', json=test["create_body"])
        assert resp.status == test["create_status"]
        resp = await client.patch(f'/couriers/{test["courier_id"]}', json=test["update_body"])
        assert resp.status == test["update_status"]
        if test["update_status"] == 200:
            json = await resp.json()
            assert json == test["result"]


async def test_orders(aiohttp_client, loop):
    app = create_application("test_database.db")
    reset_db(app['db'])
    client = await aiohttp_client(app)
    tests = [
        {
            "body": {"data": [{"order_id": 1, "weight": 0.23, "region": 10, "delivery_hours": ["09:00-12:00"]},
                              {"order_id": 2, "weight": 10, "region": 43,
                               "delivery_hours": ["12:00-15:00", "18:00-23:00"]}]},
            "status": 201,
            "result": {"orders": [{"id": 1}, {"id": 2}]},
        },
        {
            "body": {"data": [{"order_id": 1, "weight": 0.009, "region": 10, "delivery_hours": ["09:00-12:00"]},
                              {"order_id": 2, "weight": 50.1, "region": 43,
                               "delivery_hours": ["12:00-15:00", "18:00-23:00"]},
                              {"order_id": 3, "weight": 1, "region": -1, "delivery_hours": ["09:00-12:00"]},
                              {"order_id": 4, "weight": 2, "region": 12, "delivery_hours": [1, 2, 3]}]},
            "status": 400,
            "result": {"validation_error": {"orders": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]}},
        }
    ]

    for test in tests:
        resp = await client.post('/orders', json=test["body"])
        assert resp.status == test["status"]
        json = await resp.json()
        assert json == test["result"]


async def test_orders_assign(aiohttp_client, loop):
    app = create_application("test_database.db")
    client = await aiohttp_client(app)
    tests = [
        {
            "courier_body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]}]},
            "order_body": {"data": [{"order_id": 1, "weight": 0.23, "region": 1, "delivery_hours": ["09:00-12:00"]},
                                    {"order_id": 2, "weight": 10, "region": 2,
                                     "delivery_hours": ["12:00-15:00", "18:00-23:00"]}]},
            "assign_body": {"courier_id": 1},
            "final_status": 200,
            "final_resp": {"orders": [{"id": 1}]},
        },
        {
            "courier_body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]}]},
            "order_body": {"data": [{"order_id": 1, "weight": 0.23, "region": 1, "delivery_hours": ["09:00-12:00"]},
                                    {"order_id": 2, "weight": 10, "region": 2,
                                     "delivery_hours": ["12:00-15:00", "18:00-23:00"]}]},
            "assign_body": {"courier_id": 3},
            "final_status": 400,
            "final_resp": {"orders": [{"id": 1}]},
        },
        {
            "courier_body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]}]},
            "order_body": {"data": [{"order_id": 1, "weight": 0.23, "region": 1, "delivery_hours": ["09:00-12:00"]},
                                    {"order_id": 2, "weight": 0.1, "region": 2,
                                     "delivery_hours": ["12:00-15:00", "18:00-23:00"]},
                                    {"order_id": 3, "weight": 9, "region": 1,
                                     "delivery_hours": ["15:00-21:00", "23:00-23:59"]},
                                    {"order_id": 4, "weight": 0.2, "region": 1,
                                     "delivery_hours": ["09:00-10:30", "19:00-23:00"]},
                                    {"order_id": 5, "weight": 1, "region": 1, "delivery_hours": ["07:00-14:00"]}]},
            "assign_body": {"courier_id": 1},
            "final_status": 200,
            "final_resp": {"orders": [{"id": 1}, {"id": 3}]},
        }
    ]

    for test in tests:
        reset_db(app['db'])
        resp = await client.post('/couriers', json=test["courier_body"])
        assert resp.status == 201
        resp = await client.post('/orders', json=test['order_body'])
        assert resp.status == 201
        resp = await client.post('/orders/assign', json=test['assign_body'])
        assert resp.status == test['final_status']
        if test['final_status'] == 200:
            json = await resp.json()
            assert json["orders"] == test['final_resp']["orders"]
            assert datetime.datetime.strptime(json["assign_time"], "%Y-%m-%dT%H:%M:%S.%fZ").astimezone(
                datetime.timezone.utc) < datetime.datetime.now(tz=datetime.timezone.utc)


async def test_orders_complete(aiohttp_client, loop):
    app = create_application("test_database.db")
    client = await aiohttp_client(app)
    tests = [
        {
            "courier_body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]}]},
            "order_body": {"data": [{"order_id": 1, "weight": 0.23, "region": 1, "delivery_hours": ["09:00-12:00"]},
                                    {"order_id": 2, "weight": 10, "region": 2,
                                     "delivery_hours": ["12:00-15:00", "18:00-23:00"]}]},
            "assign_body": {"courier_id": 1},
            "complete_bodies": [{"courier_id": 1, "order_id": 1, "complete_time": "2021-03-21T14:22:11.21Z"},
                                {"courier_id": 1, "order_id": 1, "complete_time": "2021-03-21T14:22:11.21Z"},
                                {"courier_id": 1, "order_id": 2}, {"courier_id": 2, "order_id": 1}],
            "final_statuses": [200, 200, 400, 400],
            "final_resps": [{"order_id": 1}, {"order_id": 1}, {}, {}],
        },
        {
            "courier_body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]},
                         {"courier_id": 2, "courier_type": "car", "regions": [2, 3],
                          "working_hours": ["09:00-18:00"]}]},
            "order_body": {"data": [{"order_id": 1, "weight": 0.23, "region": 1, "delivery_hours": ["09:00-12:00"]},
                                    {"order_id": 2, "weight": 0.1, "region": 2,
                                     "delivery_hours": ["12:00-15:00", "18:00-23:00"]},
                                    {"order_id": 3, "weight": 9, "region": 1,
                                     "delivery_hours": ["15:00-21:00", "23:00-23:59"]},
                                    {"order_id": 4, "weight": 0.2, "region": 1,
                                     "delivery_hours": ["09:00-10:30", "19:00-23:00"]},
                                    {"order_id": 5, "weight": 1, "region": 1, "delivery_hours": ["07:00-14:00"]}]},
            "assign_body": {"courier_id": 1},
            "complete_bodies": [{"courier_id": 1, "order_id": 1, "complete_time": "2021-03-21T15:22:11.21Z"},
                                {"courier_id": 1, "order_id": 2},
                                {"courier_id": 1, "order_id": 3, "complete_time": "2021-03-21T16:22:11.21Z"},
                                {"courier_id": 1, "order_id": 4},
                                {"courier_id": 1, "order_id": 5}, {"courier_id": 2, "order_id": 1},
                                {"courier_id": 2, "order_id": 2}],
            "final_statuses": [200, 400, 200, 400, 400, 400, 400],
            "final_resps": [{"order_id": 1}, {}, {"order_id": 3}, {}, {}, {}, {}],
        }
    ]

    for test in tests:
        reset_db(app['db'])
        resp = await client.post('/couriers', json=test["courier_body"])
        assert resp.status == 201
        resp = await client.post('/orders', json=test['order_body'])
        assert resp.status == 201
        resp = await client.post('/orders/assign', json=test['assign_body'])
        assert resp.status == 200
        for i in range(len(test['complete_bodies'])):
            resp = await client.post('/orders/complete', json=test['complete_bodies'][i])
            assert resp.status == test['final_statuses'][i]
            if test['final_statuses'][i] == 200:
                json = await resp.json()
                assert json == test['final_resps'][i]


async def test_courier_info(aiohttp_client, loop):
    app = create_application("test_database.db")
    client = await aiohttp_client(app)
    tests = [
        {
            "courier_body": {
                "data": [{"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"]}]},
            "order_body": {"data": [{"order_id": 1, "weight": 0.23, "region": 1, "delivery_hours": ["09:00-12:00"]},
                                    {"order_id": 2, "weight": 10, "region": 2,
                                     "delivery_hours": ["12:00-15:00", "18:00-23:00"]}]},
            "assign_body": {"courier_id": 1},
            "complete_bodies": [{"courier_id": 1, "order_id": 1,
                                 "complete_time": datetime.datetime.fromtimestamp(time.time()+7200,
                                                                                  tz=datetime.timezone.utc).strftime(
                                     "%Y-%m-%dT%H:%M:%S.%fZ")}],
            "courier_ids": [1, 2],
            "final_statuses": [200, 400],
            "final_resps": [
                {"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["11:00-18:00"], "rating": 0,
                 "earnings": 1000}, {}],
        },
        {
            "courier_body": {
                "data": [{"courier_id": 1, "courier_type": "bike", "regions": [1], "working_hours": ["11:00-18:00"]},
                         {"courier_id": 2, "courier_type": "car", "regions": [2, 3],
                          "working_hours": ["09:00-18:00"]}]},
            "order_body": {"data": [{"order_id": 1, "weight": 0.23, "region": 1, "delivery_hours": ["09:00-12:00"]},
                                    {"order_id": 2, "weight": 0.1, "region": 2,
                                     "delivery_hours": ["12:00-15:00", "18:00-23:00"]},
                                    {"order_id": 3, "weight": 9, "region": 1,
                                     "delivery_hours": ["15:00-21:00", "23:00-23:59"]},
                                    {"order_id": 4, "weight": 0.2, "region": 1,
                                     "delivery_hours": ["09:00-10:30", "19:00-23:00"]},
                                    {"order_id": 5, "weight": 1, "region": 1, "delivery_hours": ["07:00-14:00"]}]},
            "assign_body": {"courier_id": 1},
            "complete_bodies": [{"courier_id": 1, "order_id": 1,
                                 "complete_time": datetime.datetime.fromtimestamp(time.time()+20,
                                                                                  tz=datetime.timezone.utc).strftime(
                                     "%Y-%m-%dT%H:%M:%S.%fZ")},
                                {"courier_id": 1, "order_id": 3,
                                 "complete_time": datetime.datetime.fromtimestamp(time.time()+10,
                                                                                  tz=datetime.timezone.utc).strftime(
                                     "%Y-%m-%dT%H:%M:%S.%fZ")}],
            "courier_ids": [1, 2],
            "final_statuses": [200, 400],
            "final_resps": [
                {"courier_id": 1, "courier_type": "bike", "regions": [1], "working_hours": ["11:00-18:00"], "rating1": 5, "rating2": 4,
                 "earnings": 2500}],
        }
    ]

    for test in tests:
        reset_db(app['db'])
        resp = await client.post('/couriers', json=test["courier_body"])
        assert resp.status == 201
        resp = await client.post('/orders', json=test['order_body'])
        assert resp.status == 201
        resp = await client.post('/orders/assign', json=test['assign_body'])
        assert resp.status == 200
        for i in range(len(test['complete_bodies'])):
            resp = await client.post('/orders/complete', json=test['complete_bodies'][i])
            assert resp.status == 200
        for i in range(len(test['courier_ids'])):
            resp = await client.get(f'/couriers/{test["courier_ids"][i]}')
            assert resp.status == test["final_statuses"][i]
            if test["final_statuses"][i] == 200:
                json = await resp.json()
                assert json["courier_id"] == test["final_resps"][i]["courier_id"]
                assert json["courier_type"] == test["final_resps"][i]["courier_type"]
                assert json["regions"] == test["final_resps"][i]["regions"]
                assert json["working_hours"] == test["final_resps"][i]["working_hours"]
                assert json["earnings"] == test["final_resps"][i]["earnings"]
                if "rating" in test["final_resps"][i]:
                    assert json["rating"] == test["final_resps"][i]["rating"]
                else:
                    assert test["final_resps"][i]["rating2"] < json["rating"] <= test["final_resps"][i]["rating1"]
