from order import Order
import time


max_weight = {"foot": 10, "bike": 15, "car": 50}


class Courier:
    def __init__(self, id, type, regions, working_hours, delivery_count):
        self.id = id
        self.type = type
        self.regions = regions
        self.working_hours = working_hours
        self.delivery_count = delivery_count

    def save(self, db):
        cur = db.cursor()
        cols_to_save = (self.id, self.type, ','.join(str(x) for x in self.regions), ','.join(self.working_hours))
        cur.execute('INSERT OR REPLACE INTO couriers(id, courier_type, regions, working_hours) VALUES(?,?,?,?)', cols_to_save)
        db.commit()

    def update(self, db):
        cur = db.cursor()
        sql = 'UPDATE couriers SET '
        params = ()
        if self.type is not None:
            sql += 'courier_type = ?,'
            params +=  (self.type,)
        if self.regions is not None:
            sql += 'regions = ?,'
            params += (','.join(str(x) for x in self.regions),)
        if self.working_hours is not None:
            sql += 'working_hours = ?,'
            params += (','.join(self.working_hours),)
        params += (self.id,)
        sql = sql[:-1] + ' WHERE id = ?'
        cur.execute(sql, params)
        db.commit()
        obj = cur.execute('select * from couriers WHERE id = ?', self.id).fetchone()
        return Courier(obj[0], obj[1], [int(x) for x in obj[2].split(',')], obj[3].split(','), 0)

    def get_compatible_orders(self, db):
        cur = db.cursor()
        cur.execute('SELECT * FROM orders WHERE courier_id = ? and complete == 0', (self.id,))
        rows = cur.fetchall()
        cur_weight = 0
        cur_orders = []
        for row in rows:
            order = Order(row[0], row[1], row[2], row[3].split(','), row[4], row[5], row[6])
            cur_weight += order.weight
            cur_orders.append(order)

        cur.execute('SELECT * FROM orders WHERE courier_id is null and complete == 0')
        rows = cur.fetchall()
        for row in rows:
            order = Order(row[0], row[1], row[2], row[3].split(','), None, row[5], row[6])
            if order.weight + cur_weight <= max_weight[self.type] and order.region in self.regions and check_delivery_time(self.working_hours, order.delivery_hours):
                cur_weight += order.weight
                cur_orders.append(order)
        return cur_orders

    def get_incompatible_orders(self, db):
        cur = db.cursor()
        cur.execute('SELECT * FROM orders WHERE courier_id = ? and complete == 0', (self.id,))
        rows = cur.fetchall()
        cur_weight = 0
        excess_orders = []
        for row in rows:
            order = Order(row[0], row[1], row[2], row[3].split(','), row[4], row[5], row[6])
            if order.weight + cur_weight <= max_weight[self.type] and order.region in self.regions and check_delivery_time(self.working_hours, order.delivery_hours):
                cur_weight += order.weight
            else:
                excess_orders.append(order)
        return excess_orders

    def increase_delivery_count(self, db):
        cur = db.cursor()
        self.delivery_count += 1
        cur.execute('UPDATE couriers SET delivery_count = ? WHERE id = ?', (self.delivery_count, self.id))
        db.commit()

    def get_min_average_delivery_time(self, db):
        cur = db.cursor()
        cur.execute('''
                    SELECT 
                        avg(completed_time - assigned_time) 
                    FROM orders 
                    WHERE courier_id = ? AND complete = 1 GROUP BY region''', (self.id,))
        rows = cur.fetchall()
        min_time = None
        for row in rows:
            if min_time is None:
                min_time = row[0]
            else:
                if min_time > row[0]:
                    min_time = row[0]
        return min_time


def check_delivery_time(working_intervals, delivery_intervals):
    for working_interval in working_intervals:
        working_times = [time.strptime(time_str, '%H:%M') for time_str in working_interval.split('-')]
        for delivery_time in delivery_intervals:
            delivery_times = [time.strptime(time_str, '%H:%M') for time_str in delivery_time.split('-')]
            if working_times[0] <= delivery_times[0] < working_times[1] or working_times[0] < delivery_times[1] <= working_times[1]:
                return True
    return False


def get_courier(id, db):
    cur = db.cursor()
    row = cur.execute('SELECT * FROM couriers WHERE id = ?', (id,)).fetchone()
    if row is None:
        return None
    else:
        return Courier(row[0], row[1], [int(x) for x in row[2].split(',')], row[3].split(','), row[4])
