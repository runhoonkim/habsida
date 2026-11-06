-- =============================================================================
-- shared course database  —  SEED DATA
-- =============================================================================
-- Synthetic but realistic data, generated inside the database with
-- generate_series() + random(), so this file stays small while producing a
-- dataset large enough for joins, GROUP BY, and aggregations to be interesting:
--
--     1,000 users    200 products    30,000 orders    ~30 documents
--
-- Run AFTER schema.sql:
--   docker exec -i pg psql -U postgres < seed.sql
-- =============================================================================

-- Fix the random seed so everyone in the class generates the SAME data.
SELECT setseed(0.42);

-- Empty the tables and reset id counters (safe to re-run).
TRUNCATE orders, documents, products, users RESTART IDENTITY CASCADE;

-- -----------------------------------------------------------------------------
-- users  —  1,000 accounts
-- email is unique via the row number; ~3% are admins.
--
-- Every demo user shares the SAME password: "password123". The string below is a
-- real bcrypt hash of that password (cost 12), so the token/password login built
-- in the REST API chapter actually works against this seed data — e.g. log in as
-- user1@example.com with password "password123". Real hashing is taught in the
-- auth chapter; here we just need a hash that genuinely verifies.
-- -----------------------------------------------------------------------------
INSERT INTO users (email, hashed_password, full_name, role, created_at)
SELECT
    'user' || g || '@example.com',
    '$2b$12$b6bPEw1xNH6aJD3w2wCYq.KYHPLabY2zJKProNUmSGOiZIppQl5zO',  -- bcrypt("password123")
    (ARRAY['Ada','Grace','Linus','Alan','Edsger','Donald','Barbara','Margaret',
           'Ken','Dennis','Guido','James','Bjarne','John','Tim','Brian'])
        [1 + floor(random() * 16)::int]
    || ' ' ||
    (ARRAY['Lovelace','Hopper','Torvalds','Turing','Dijkstra','Knuth','Liskov',
           'Hamilton','Thompson','Ritchie','Rossum','Gosling','Stroustrup',
           'McCarthy','Berners-Lee','Kernighan'])
        [1 + floor(random() * 16)::int],
    CASE WHEN random() < 0.03 THEN 'admin' ELSE 'member' END,
    now() - (random() * interval '730 days')
FROM generate_series(1, 1000) AS g;

-- -----------------------------------------------------------------------------
-- products  —  200 catalog items across 5 categories
-- -----------------------------------------------------------------------------
INSERT INTO products (name, category, description, price, stock, created_at)
SELECT
    (ARRAY['Aero','Nova','Pulse','Vertex','Lumen','Atlas','Orbit','Quartz'])
        [1 + floor(random() * 8)::int]
    || ' ' ||
    (ARRAY['Keyboard','Monitor','Mouse','Webcam','Headset','Desk Lamp',
           'Laptop Stand','Office Chair','Notebook','Backpack','Water Bottle',
           'Desk Mat'])
        [1 + floor(random() * 12)::int]
    || ' ' || g,
    (ARRAY['Electronics','Accessories','Furniture','Office','Lifestyle'])
        [1 + floor(random() * 5)::int],
    'Sample product used for course exercises.',
    round((random() * 480 + 5)::numeric, 2),
    floor(random() * 500)::int,
    now() - (random() * interval '365 days')
FROM generate_series(1, 200) AS g;

-- -----------------------------------------------------------------------------
-- orders  —  30,000 purchases
-- Each references a random valid user (1..1000) and product (1..200).
-- Status is weighted toward completed orders to look like real traffic.
-- -----------------------------------------------------------------------------
INSERT INTO orders (user_id, product_id, quantity, status, created_at)
SELECT
    1 + floor(random() * 1000)::int,
    1 + floor(random() * 200)::int,
    1 + floor(random() * 5)::int,
    (ARRAY['pending','paid','paid','shipped','shipped','delivered','delivered',
           'delivered','delivered','cancelled'])
        [1 + floor(random() * 10)::int],
    now() - (random() * interval '365 days')
FROM generate_series(1, 30000);

-- -----------------------------------------------------------------------------
-- documents  —  a small, realistic help-centre corpus for the RAG chapter.
-- embedding stays NULL here; the LLM chapter fills it with a real embedding model.
-- -----------------------------------------------------------------------------
INSERT INTO documents (title, content, source, metadata) VALUES
('Shipping policy',
 'We ship all in-stock orders within 2 business days. Standard delivery takes 3-5 business days; express delivery arrives the next business day. You receive a tracking link by email as soon as your order ships.',
 'help-center', '{"topic":"shipping"}'),
('International shipping',
 'We currently ship to most countries in Europe and North America. International orders may take 7-14 business days and can be subject to customs duties, which are the responsibility of the recipient.',
 'help-center', '{"topic":"shipping"}'),
('Return policy',
 'Unused items in their original packaging can be returned within 30 days of delivery for a full refund. Start a return from your account''s Orders page; we email a prepaid shipping label once the request is approved.',
 'help-center', '{"topic":"returns"}'),
('Refund timing',
 'Refunds are issued to your original payment method within 5-7 business days after we receive and inspect the returned item. You will get an email confirmation when the refund is processed.',
 'help-center', '{"topic":"returns"}'),
('Exchanges',
 'We do not offer direct exchanges. To swap an item for a different size or model, return the original for a refund and place a new order. This keeps the process fast and transparent.',
 'help-center', '{"topic":"returns"}'),
('Warranty coverage',
 'Electronics come with a 1-year limited warranty covering manufacturing defects. The warranty does not cover accidental damage, water damage, or normal wear. Keep your order confirmation as proof of purchase.',
 'help-center', '{"topic":"warranty"}'),
('Damaged on arrival',
 'If your item arrives damaged, contact support within 48 hours with photos of the product and packaging. We will send a replacement at no cost or issue a full refund, whichever you prefer.',
 'help-center', '{"topic":"warranty"}'),
('Accepted payment methods',
 'We accept Visa, Mastercard, American Express, and PayPal. Payment is captured when your order ships, not when it is placed. We never store full card numbers on our servers.',
 'help-center', '{"topic":"payments"}'),
('Payment declined',
 'A declined payment is usually caused by an incorrect billing address, insufficient funds, or a bank security hold. Double-check your details and try again, or contact your bank if the problem persists.',
 'help-center', '{"topic":"payments"}'),
('Creating an account',
 'Click Sign Up, enter your email and a strong password, and verify your email address through the link we send. An account lets you track orders, save addresses, and start returns.',
 'help-center', '{"topic":"account"}'),
('Resetting your password',
 'On the login page, choose Forgot Password and enter your email. We send a secure reset link valid for one hour. For your safety, password reset links can only be used once.',
 'help-center', '{"topic":"account"}'),
('Updating your address',
 'Open Account > Addresses to add or edit shipping addresses. Changing an address does not affect orders that have already shipped. The default address is used to pre-fill checkout.',
 'help-center', '{"topic":"account"}'),
('Order status meanings',
 'Pending means we have received your order but not yet charged it. Paid means payment succeeded. Shipped means it is on the way. Delivered means it arrived. Cancelled means the order was voided and not charged.',
 'help-center', '{"topic":"orders"}'),
('Cancelling an order',
 'You can cancel an order for free while it is still Pending or Paid. Once an order is Shipped it can no longer be cancelled, but you may return it after delivery under our return policy.',
 'help-center', '{"topic":"orders"}'),
('Tracking your order',
 'Open the order from your Orders page to see its current status and tracking link. Tracking information can take up to 24 hours to appear after an order is marked Shipped.',
 'help-center', '{"topic":"orders"}'),
('Out-of-stock items',
 'When an item shows zero stock you can join its waitlist to be emailed when it returns. Popular electronics are usually restocked within two weeks.',
 'help-center', '{"topic":"catalog"}'),
('Keyboard care guide',
 'Keep your keyboard clean by unplugging it and using compressed air between the keys. Avoid eating over the keyboard. Most keycaps can be gently removed and washed with mild soap and dried fully before refitting.',
 'product-guide', '{"category":"Electronics"}'),
('Monitor setup tips',
 'Position your monitor an arm''s length away with the top of the screen at eye level to reduce neck strain. Lower the brightness to match your room and enable night mode in the evening for comfort.',
 'product-guide', '{"category":"Electronics"}'),
('Webcam privacy',
 'Our webcams include a physical privacy shutter. Slide it closed when the camera is not in use. The indicator light is hard-wired to the sensor, so it always shows when the camera is active.',
 'product-guide', '{"category":"Electronics"}'),
('Office chair assembly',
 'Attach the wheels to the base first, then the gas cylinder, then the seat and backrest. Hand-tighten all bolts before fully torquing them. Assembly takes about 15 minutes with the included tool.',
 'product-guide', '{"category":"Furniture"}'),
('Desk lamp brightness',
 'The desk lamp has three brightness levels and two colour temperatures. Tap the touch panel to cycle brightness; hold it to switch between warm and cool light. It remembers your last setting.',
 'product-guide', '{"category":"Office"}'),
('Backpack water resistance',
 'The backpack fabric is water-resistant, not waterproof. It handles light rain, but in heavy downpours use the included rain cover. Do not machine wash; spot-clean with a damp cloth instead.',
 'product-guide', '{"category":"Lifestyle"}'),
('Water bottle cleaning',
 'Hand-wash the bottle daily with warm soapy water and let it air-dry upside down. The lid is dishwasher-safe on the top rack. Do not put boiling liquids in an insulated bottle.',
 'product-guide', '{"category":"Lifestyle"}'),
('Bulk and business orders',
 'For orders over 25 units, contact our business team for volume pricing and consolidated invoicing. Business accounts can also request net-30 payment terms after a credit check.',
 'help-center', '{"topic":"business"}'),
('Gift options',
 'At checkout you can mark an order as a gift to hide prices on the packing slip and add a short message. Gift receipts let the recipient return items without seeing the original price.',
 'help-center', '{"topic":"orders"}'),
('Loyalty points',
 'You earn one point per dollar spent on delivered orders. Every 100 points is worth a five-dollar discount at checkout. Points expire 12 months after they are earned.',
 'help-center', '{"topic":"account"}'),
('Privacy of your data',
 'We store only the data needed to fulfil your orders and never sell it. You can request a copy or deletion of your personal data at any time from Account > Privacy.',
 'help-center', '{"topic":"privacy"}'),
('Contacting support',
 'Reach support by email at help@example.com or via live chat from 9am to 6pm on weekdays. Most email enquiries are answered within one business day.',
 'help-center', '{"topic":"support"}'),
('Price matching',
 'If you find the same item cheaper at a major retailer within 14 days of purchase, contact support with a link and we will refund the difference, subject to verification.',
 'help-center', '{"topic":"payments"}'),
('Sustainability',
 'We use recyclable packaging and consolidate shipments to cut emissions. Electronics can be returned at end of life through our free recycling program; request a label from support.',
 'help-center', '{"topic":"sustainability"}');
