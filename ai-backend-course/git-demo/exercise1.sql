/* 1. All admins
 * Write a query that returns the email and full_name of every user whose role is 'admin'. 
 */

select
  u.email,
  u.full_name 

from users u

where role = 'admin';



/* 
 * 2. Affordable electronics
 * Write a query that returns name and price 
 * for every product in the 'Electronics' category 
 * priced under $50, cheapest first.
 */

select 
  p.name,
  p.price   
from products p
where p.category  = 'Electronics'
  and p.price < 50
order by p.price asc;

/*
 * 3. The newest accounts
 * Write a query that returns the email and created_at 
 * of the 10 most recently created user accounts, 
 * newest first.
 */

select 
  u.email,
  u.created_at 
from users u
order by u.created_at desc
limit 10;

/*
 * 4. Keyboards only
 * Write a query that returns name, category, and price 
 * for every product whose name contains the word Keyboard, 
 * sorted alphabetically by name.
 */

select
  p.name,
  p.category,
  p.price
from products p
where p.name like '%Keyboard%'
order by p.name asc;

/*
 * 5. Names starting with "A"
 * Write a query that returns the full_name and email of every user 
 * whose full_name starts with the letter A.
 */

select 
  u.full_name,
  u.email 
from users u
where u.full_name like 'A%';

/*
 * 6. Cheapest furniture
 * Write a query that returns the 5 cheapest products in the 'Furniture' category 
 * — name and price only, cheapest first.
 */

select
  p.name,
  p.price
from products p
where p.category = 'Furniture'
order by p.price asc
limit 5;

/*
 * 7. A mid-range price band
 * Write a query that returns name, category, and price 
 * for products priced between 100 and 200 inclusive, 
 * most expensive first, limited to the top 10.
 */

select 
  p.name,
  p.category,
  p.price
from products p
where p.price between 100 and 200
order by p.price desc
limit 10;

/*
 * 8. The "second page" of expensive products
 * Write a query that returns products 6th through 10th most expensive overall 
 * (name, price).
 */
select 
  p.name,
  p.price
from products p
order by p.price desc
limit 5
offset 5;

/*
 * 9. Conceptual: keys, not code
No SQL for this one — answer in a sentence or two.

Q:
users and products are both standalone tables so far, with no orders table yet in the picture. 
Once orders exists (next lesson), which column in users would a foreign key in orders most likely point to, and why does that column make a good primary key in the first place?

A:
The `id` key in the users table would be the best choice because the `id` key is an unique and not null value.
The `user_id` column in the `orders` table hints that it will be joined to the `id` column in the `user` table.
The `email` column is not an ideal choice considering the possibility that it might be changed over time.    
 */