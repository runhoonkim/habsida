-- Check connection
SELECT * FROM users LIMIT 10;

CREATE TABLE lesson_products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT now()    
);

SELECT * FROM lesson_products
ORDER BY id;

INSERT INTO lesson_products (name, price, stock) VALUES 
    ('Desk Lamp', 34.95, 80);

INSERT INTO lesson_products (name, price, stock) VALUES 
    ('Cable', 9.99, 500),
    ('Stand', 59.00, 40),
    ('Webcam', 79.99, 0);

INSERT INTO lesson_products (name, price, stock) VALUES 
    ('Notebook', 12.50, 100)
    RETURNING id;

SELECT * FROM lesson_products
WHERE name = 'Webcam';

UPDATE lesson_products
SET stock = 50
WHERE name = 'Webcam';

SELECT * FROM lesson_products
WHERE name = 'Desk Lamp';

UPDATE lesson_products
SET price = 39.95
WHERE name = 'Desk Lamp';

SELECT * FROM lesson_products
WHERE name = 'Cable';

DELETE FROM lesson_products
WHERE name = 'Cable';

SELECT * FROM lesson_products;

ALTER TABLE lesson_products
ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;

UPDATE lesson_products
SET is_active = FALSE
WHERE name = 'Stand';

SELECT * FROM lesson_products
WHERE is_active = TRUE;