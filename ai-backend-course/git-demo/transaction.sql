BEGIN;

UPDATE lesson_products
SET stock = stock - 1
WHERE name = 'Desk Lamp';

COMMIT;

SELECT name, stock
FROM lesson_products
WHERE name = 'Desk Lamp';

ROLLBACK;

SELECT name, stock
FROM lesson_products
WHERE name = 'Desk Lamp';

DROP TABLE IF EXISTS lesson_products;
