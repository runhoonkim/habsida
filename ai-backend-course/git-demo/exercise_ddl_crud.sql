/* Careful: several of these questions write to your database.
If you want a clean slate afterward, you can always reload it: 
docker exec -i pg psql -U postgres < schema.sql then seed.sql again 
(this drops and recreates every table).
*/

SELECT
  (SELECT count(*) FROM users)     AS users,
  (SELECT count(*) FROM products)  AS products,
  (SELECT count(*) FROM orders)    AS orders,
  (SELECT count(*) FROM documents) AS documents;

/*
Setup
-- users:    id, email, hashed_password, full_name, role, created_at
-- products: id, name, category, description, price, stock, created_at
-- orders:   id, user_id, product_id, quantity, status, created_at
*/

/*
Questions
*/

-- 1. Design a reviews table
-- Write the CREATE TABLE statement for a new reviews table where a user can leave one review per product: 
-- a rating from 1 to 5, an optional text comment, and a timestamp. Your table must guarantee, using constraints alone (no application code):

-- a review always references a real user and a real product;
-- the same user cannot review the same product twice;
-- rating can never be outside the range 1-5.
-- Hint: "the same user cannot review the same product twice" is exactly the composite-key pattern from the favorites example in the lesson.

BEGIN;

CREATE TABLE reviews (
    user_id     INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, product_id),

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

SELECT * FROM reviews;

COMMIT;

-- 2. Add a column
-- Write an ALTER TABLE statement that adds a nullable phone_number column (TEXT) to users.

BEGIN;

ALTER TABLE users 
ADD COLUMN phone_number TEXT;

COMMIT;

-- 3. Add a constraint after the fact
-- Write an ALTER TABLE statement that adds a CHECK constraint to orders 
-- requiring quantity to be at most 10 (it already must be greater than 0 from the original schema).
BEGIN;

ALTER TABLE orders
ADD CONSTRAINT max_quantity CHECK (quantity <= 10);

COMMIT;

-- 4. Insert a product
-- Write an INSERT statement that adds a new product: 
-- name 'Studio Desk Lamp', category 'Office', price 45.50, stock 25. 
-- Use RETURNING so the statement gives you back the new row's id.

BEGIN;

INSERT INTO products (name, category, price, stock) 
VALUES
    ('Studio Desk Lamp', 'Office', 45.50, 25)
RETURNING id;

COMMIT;

-- 5. A catalog-wide price increase
-- Write an UPDATE statement that raises the price of every product 
-- in the 'Furniture' category by 10% (i.e. multiply price by 1.10).

-- Reminder: always look at your WHERE clause twice before running an UPDATE. 
-- What would this statement do to your data if you forgot the WHERE entirely?

BEGIN;

SELECT *
FROM products
WHERE category = 'Furniture';

UPDATE products
SET price = price * 1.1
WHERE category = 'Furniture';

COMMIT;

-- 6. Auto-cancel stale orders
-- Write an UPDATE statement that sets status to 'cancelled' for every order 
-- that is still 'pending' and was created more than 30 days ago.

-- Hint: compare created_at against now() - interval '30 days'.

BEGIN;

SELECT *
FROM ORDERS 
WHERE status = 'pending'
  AND created_at < NOW() - INTERVAL '30 days';

UPDATE ORDERS 
SET status = 'cancelled'
WHERE status = 'pending'
  AND created_at < NOW() - INTERVAL '30 days';

COMMIT;

-- 7. Delete, and explain the failure
-- Pick any product that has at least one order referencing it (check with a SELECT first), then try to DELETE it. 
-- Write down the error message Postgres gives you, and explain why it happens in one sentence, 
-- referencing a concept from the previous lesson.

BEGIN;

SELECT p.*, o.id AS order_id
FROM products p
LEFT OUTER JOIN orders o
ON o.product_id = p.id
WHERE o.id IS NOT NULL
LIMIT 1;

DELETE FROM products
WHERE id = 58;

ROLLBACK;

/*
Error message:
update or delete on table "products" violates foreign key constraint "orders_product_id_fkey" on table "orders"
DETAIL: Key (id)=(58) is still referenced from table "orders".

Explanation:
In orders table, the product_id has a constraint REFERENCES products(id), thereby constraining product_id to match a row in the product table,
so we cannot delete a product that has an order referencing to it, before deleting the orders first.
*/

-- 8. Indexing a new query pattern
-- Your application now frequently runs: SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at;. 
-- Write a CREATE INDEX statement that would speed this query up.

-- Hint: an index can cover more than one column — look up how to create a multi-column index in the PostgreSQL docs 
-- if you want to go further than a single-column one.

BEGIN;

CREATE INDEX idx_orders_status_created_at
ON orders (status, created_at);

COMMIT;

-- 9. A safe restock-and-order transaction
-- Write a transaction (BEGIN … COMMIT) that does two things atomically: 
-- inserts a new order for user 1 buying 2 units of product 1, 
-- and decrements product 1's stock by 2. 
-- If either statement would fail, neither should take effect.
SELECT * FROM orders LIMIT 5;

SELECT * FROM products
WHERE id = 1;

BEGIN;

INSERT INTO orders (user_id, product_id, quantity) 
VALUES (1, 1, 2);

UPDATE products
SET stock = stock - 2
WHERE id = 1;

COMMIT;