import time


class Order:
    def __init__(self, id, weight, region, delivery_hours, courier_id, complete, assign_time):
        self.id = id
        self.weight = weight
        self.region = region
        self.delivery_hours = delivery_hours
        self.courier_id = courier_id
        self.complete = complete
        self.assign_time = assign_time

    def save(self, db):
        cur = db.cursor()
        cols_to_save = (self.id, self.weight, self.region, ','.join(self.delivery_hours))
        cur.execute('INSERT OR REPLACE INTO orders(id, weight, region, delivery_hours) VALUES(?,?,?,?)', cols_to_save)
        db.commit()

    def set_courier(self, db, id, assign_time):
        cur = db.cursor()
        cur.execute('UPDATE orders SET courier_id = ?, assigned_time = ? WHERE id = ?', (id, assign_time, self.id))
        db.commit()

    def set_complete(self, db, complete_time):
        cur = db.cursor()
        cur.execute('UPDATE orders SET complete = 1, completed_time = ? WHERE id = ?', (complete_time.timestamp(), self.id))
        db.commit()

    def remove_courier(self, db):
        cur = db.cursor()
        cur.execute('UPDATE orders SET courier_id = null, assign_time = null WHERE id = ?', (self.id,))
        db.commit()


def get_order(id, db):
    cur = db.cursor()
    row = cur.execute('SELECT * FROM orders WHERE id = ?', (id,)).fetchone()
    if row is None:
        return None
    else:
        return Order(row[0], row[1], row[2], row[3].split(','), row[4], row[5], row[6])
