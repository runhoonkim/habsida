-- =============
-- SETUP
-- =============

-- You'll need all three tables this time:

-- users:    id, email, hashed_password, full_name, role, created_at
-- products: id, name, category, description, price, stock, created_at
-- orders:   id, user_id, product_id, quantity, status, created_at

-- orders.status is one of 'pending', 'paid', 'shipped', 'delivered', 'cancelled'.


-- run this once to guarantee there's something for those two queries to find:
INSERT INTO users (email, hashed_password, full_name, role)
VALUES ('never_ordered@example.com', 'not-a-real-hash', 'No Orders Yet', 'member')
ON CONFLICT (email) DO NOTHING;

INSERT INTO products (name, category, price, stock)
SELECT 'Unreleased Prototype', 'Electronics', 999.99, 0
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Unreleased Prototype');

-- =============
-- QUESTIONS
-- =============

-- 1. Who ordered what
-- Write a query that joins orders to users and products to return, 
-- for every order: the order's id, the user's email, the product's name, and the order's quantity.

SELECT
  o.id,
  u.email,
  p.name,
  o.quantity 
FROM orders o
INNER JOIN users u ON u.id = o.user_id
INNER JOIN products p ON p.id = o.product_id;

-- 2. Sorted by order day
-- Extend question 1: also select the date the order was placed 
-- (just the day, not the full timestamp — orders.created_at is a TIMESTAMPTZ), 
-- and sort the whole result by that day, earliest first.

-- Hint: you need a function that extracts just the date part from a timestamp column. Look up PostgreSQL's DATE() function or a cast with ::date.
SELECT
  o.id,
  u.email,
  p.name,
  o.quantity,
  DATE(o.created_at) AS order_date
FROM orders o
INNER JOIN users u ON u.id = o.user_id
INNER JOIN products p ON p.id = o.product_id
ORDER BY order_date ASC;

-- 3. Users who never ordered
-- Write a query that returns the email of every user who has never placed a single order. 
-- (You should see the account from the Setup step, and possibly a few others.)
SELECT 
  u.email
FROM users u
LEFT OUTER JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL;

-- 4. Orders per status
-- Write a query that returns each distinct status value 
-- and how many orders currently have that status, 
-- most common status first.

SELECT 
  o.status,
  COUNT(*) AS status_count
FROM orders o
GROUP BY o.status
ORDER BY status_count DESC;

-- 5. Revenue by category
-- Write a query that returns each product category and the total revenue it has generated 
-- that is, the sum of price * quantity across every order for products in that category — sorted from highest revenue to lowest.

-- Hint: you'll need to join orders to products before you can group by category.

SELECT
  p.category,
  SUM(p.price * o.quantity) AS total_revenue

FROM orders o

INNER JOIN products p ON p.id = o.product_id

GROUP BY p.category

ORDER BY total_revenue DESC;

-- 6. Top 5 customers
-- Write a query that returns the email of the 5 users who have ordered the most items in total 
-- (sum of quantity across all their orders, regardless of status), along with that total, 
-- highest first.

SELECT
    u.email,
    SUM(o.quantity) AS total_order_quantity

FROM users u

INNER JOIN orders o ON o.user_id = u.id

GROUP BY u.email

ORDER BY total_order_quantity DESC

LIMIT 5;

-- 7. Above-average categories
-- Write a query that returns every product category 
-- whose average price is higher than the average price across the entire catalog.

-- Hint: this needs a subquery — compute the overall average once, then compare each category's average against it. 
-- Decide whether that comparison belongs in WHERE or HAVING.


SELECT t1.category
FROM (
    SELECT 
        p1.category,
        AVG(p1.price) AS cat_avg_price
    FROM products p1

    GROUP BY p1.category

    HAVING AVG(p1.price) > (SELECT AVG(p2.price) FROM products p2)
) t1;

-- 8. Frequent buyers
-- Write a query that returns the email of every user 
-- who has placed more than 40 orders (any status),
-- along with their order count, 
-- most orders first.

SELECT 
    u.email,
    COUNT(o.id) AS total_order_count

FROM users u

INNER JOIN orders o ON u.id = o.user_id

GROUP BY u.email

HAVING COUNT(o.id) > 40

ORDER BY total_order_count DESC;

-- 9. Never-ordered products
-- Write a query that returns the name of every product that has never appeared in a single order 
-- — not even a cancelled one. (You should see the product from the Setup step, and possibly a few others.)

SELECT 
    p.name

FROM products p

LEFT OUTER JOIN orders o ON o.product_id = p.id

WHERE o.id IS NULL;

