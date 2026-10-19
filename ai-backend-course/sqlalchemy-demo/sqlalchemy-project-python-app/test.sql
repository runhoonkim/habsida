SELECT * FROM users LIMIT 5;
SELECT * FROM products WHERE name = 'Aero Headset 97';
SELECT * FROM orders LIMIT 5;

SELECT
    (SELECT id FROM users WHERE email = 'user1@example.com') AS user_id,
    (SELECT id FROM products WHERE name = 'Orbit Backpack 1') AS product_id,
    (SELECT stock FROM products WHERE name = 'Orbit Backpack 1') AS stock;

-- TODO: SELECT name, price, stock FROM products ORDER BY name

SELECT
    u.email,
    t.total_orders

FROM users u

INNER JOIN (
    SELECT
        user_id,
        SUM(quantity) AS total_orders

    FROM orders

    GROUP BY user_id

    ORDER BY total_orders DESC

    LIMIT 3
) t

ON u.id = t.user_id

ORDER BY t.total_orders DESC;
