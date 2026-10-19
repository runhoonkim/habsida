# SQLAlchemy Store Project

A simple Python store application using **SQLAlchemy** and **PostgreSQL**.

The application can:

- Connect to a PostgreSQL database
- Display store statistics and product information
- Display low-stock products
- Find users who have never placed an order
- Add new products
- Place orders and automatically reduce product stock
- Protect product stock from concurrent orders using `SELECT ... FOR UPDATE`

## 1. Requirements

Make sure you have:

- Python 3.10+
- PostgreSQL
- Git

Install the required Python packages:

```bash
pip install sqlalchemy psycopg2-binary python-dotenv
```

If you are using a virtual environment, activate it first:

```bash
source .venv/bin/activate
```

## 2. Configure the database

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DATABASE
```

Replace the username, password, and database name with your PostgreSQL settings.

Do not commit `.env` to Git. Make sure it is included in `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
data/
```

## 3. Set up the database

Make sure PostgreSQL is running and that the required tables exist:

- `users`
- `products`
- `orders`

The application expects the tables to contain the columns used by the SQL queries in the Python program.

## 4. Run the application

From the project directory, run:

```bash
python main.py
```

The application first verifies the database connection and displays the store dashboard.

You will then see a menu similar to:

```text
=== Menu ===
1. Add product
2. Place order
3. Exit
```

### Add a product

Select:

```text
1
```

Then enter:

```text
Product name: Keyboard
Category: Electronics
Price: 49.99
Stock: 20
```

The application validates the price and stock before inserting the product.

### Place an order

Select:

```text
2
```

Then enter:

```text
Customer email: user1@example.com
Product name: Keyboard
Quantity: 2
```

The application checks that:

- The user exists
- The product exists
- The quantity is greater than zero
- Enough stock is available

The order and stock update are performed in the same transaction.

## 5. Database connection errors

The application verifies the database connection when it starts.

If PostgreSQL is unavailable or `DATABASE_URL` is incorrect, the application displays an error message instead of crashing unexpectedly.

## 6. Concurrent orders

When placing an order, the application uses:

```sql
SELECT ... FOR UPDATE
```

to lock the selected product row until the transaction finishes.

This prevents multiple simultaneous orders from reading the same stock value and overselling the product.