CREATE TABLE couriers(id integer primary key, courier_type text, regions text, working_hours text, delivery_count integer default 0);
CREATE TABLE orders(id integer primary key, weight real, region integer, delivery_hours text, courier_id integer, complete integer default 0, assigned_time integer, completed_time integer, foreign key(courier_id) references couriers(id) on delete cascade);