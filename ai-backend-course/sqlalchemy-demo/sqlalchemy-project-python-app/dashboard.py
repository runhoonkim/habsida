import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()


def get_engine():
    """Create and return a SQLAlchemy engine from DATABASE_URL."""
    url = os.getenv("DATABASE_URL")
    # TODO: create the engine; handle a missing URL gracefully
    if not url:
        raise ValueError("DATABASE_URL is missing in the .env file.")

    return create_engine(url)


def store_report(engine):
    """Print counts, the catalog, and the top 3 customers."""
    with engine.connect() as conn:
        # TODO: COUNT(*) on users, products, orders
        row_counts = conn.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM users) AS users_count,
                (SELECT COUNT(*) FROM products) AS products_count,
                (SELECT COUNT(*) FROM orders) AS orders_count
        """))

        row = row_counts.fetchone()

        users_count = row.users_count
        products_count = row.products_count
        orders_count = row.orders_count

        print("=== Store Dashboard ===")
        print(f"Users: {users_count} | Products: {products_count} | Orders: {orders_count}")
        print()

        # TODO: SELECT name, price, stock FROM products ORDER BY name
        catalog = conn.execute(text("""
            SELECT
                p.name,
                p.price,
                p.stock,
                COALESCE(SUM(o.quantity * p.price), 0) AS total_revenue
            FROM products p
            LEFT JOIN orders o
                ON p.id = o.product_id
            GROUP BY p.id, p.name, p.price, p.stock
            ORDER BY p.name;
        """))

        rows = catalog.fetchall()
        print("Catalog:")
        for row in rows:
            price = f"${row.price:.2f}"
            total_revenue = f"${row.total_revenue:.2f}"
            print(f"  {row.name:<23} {price:>11}          (stock {row.stock:<3})          (total_revenue {total_revenue:>11})")
        print()

        # TODO: top 3 customers by SUM(quantity) via a join + GROUP BY
        top_3 = conn.execute(text("""
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

            ORDER BY t.total_orders DESC
        """))

        rows = top_3.fetchall()
        print("Top customers:")
        for row in rows:
            print(f"  {row.email:<20}  - {row.total_orders} items")

def low_stock_alert(engine):
    with engine.connect() as conn:
        low_stock = conn.execute(text("""
            SELECT 
                name, price, stock 
            FROM products 
            WHERE stock < 10
        """))

        rows = low_stock.fetchall()
        
        print()
        print("Items with stock smaller than 10EA:")
        for row in rows:
            price = f"${row.price:.2f}"
            print(f"  {row.name:<23} {price:>10}          (stock {row.stock})")

def no_order_user(engine):
    with engine.connect() as conn:
        no_order_users = conn.execute(text("""
            SELECT 
                u.email, 
                u.full_name,
                u.role

            FROM users u

            LEFT OUTER JOIN orders o 
                ON u.id = o.user_id

            WHERE o.id IS NULL
        """))

        rows = no_order_users.fetchall()
        if rows:
            print()
            print("Never ordered users:")
            for row in rows:
                print(f"  {row.email:<20}  {row.full_name:<20}  {row.role:<6}")
        else:
            print()
            print("Never ordered users:")
            print("  No users have been found who never placed an order.")

def add_product(engine, name, category, price, stock):
    """INSERT a product and return its new id."""
    with engine.begin() as conn:   # begin() commits automatically at the end
        # TODO: INSERT ... RETURNING id, with named parameters (include category)
        added_product = conn.execute(text("""
            INSERT INTO products (name, category, price, stock)
            VALUES (:name, :category, :price, :stock)
            RETURNING id
        """), {"name": name, "category": category, "price": price, "stock": stock})

        return added_product.fetchone().id

def place_order(engine, email, product_name, quantity):
    """Create an order and decrement stock in one transaction."""
    with engine.begin() as conn:   # begin() commits on success, rolls back on error
        # TODO: look up user_id by email and product (id + stock) by name
        info = conn.execute(text("""
            SELECT
                (SELECT id FROM users WHERE email = :email) AS user_id,
                (SELECT id FROM products WHERE name = :product_name) AS product_id,
                (SELECT stock FROM products WHERE name = :product_name) AS stock
        """), {"email": email, "product_name": product_name})

        row = info.fetchone()

        user_id = row.user_id
        product_id = row.product_id
        stock = row.stock

        # Additionally raise errors when user_id or product_id is None or quantity is equal to or smaller than 0 to prevent from crashing
        if user_id is None:
            raise ValueError(f"User not found: {email}")

        if product_id is None:
            raise ValueError(f"Product not found: {product_name}")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0.")

        # TODO: if stock < quantity, raise an error to trigger rollback
        if stock < quantity:
            raise ValueError(
                f"Not enough stock for {product_name}."
                f"Available: {stock}, requested: {quantity}."
            )


        # TODO: INSERT the order, then UPDATE the product's stock
        # Insert the order
        conn.execute(text("""
            INSERT INTO orders (user_id, product_id, quantity)
            VALUES (:user_id, :product_id, :quantity)
        """), {
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity
        })

        # Update product's stock
        conn.execute(text("""
            UPDATE products
            SET stock = stock - :quantity
            WHERE id = :product_id
        """), {
            "quantity": quantity,
            "product_id": product_id
        })

        print(
            f"Order placed: {email} bought "
            f"{quantity} x {product_name}"
        )


def main():
    engine = get_engine()
    store_report(engine)
    low_stock_alert(engine)
    no_order_user(engine)
    # TODO: a small menu to add a product or place an order

    while True:
        print("\n=== Menu ===")
        print("1. Add product")
        print("2. Place order")
        print("3. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            name = input("Product name: ")
            category = input("Category: ")
            price = float(input("Price: "))
            stock = int(input("Stock: "))

            product_id = add_product(
                engine,
                name,
                category,
                price,
                stock
            )

            print(f"Product added with id {product_id}.")

        elif choice == "2":
            email = input("Customer email: ")
            product_name = input("Product name: ")
            quantity = int(input("Quantity: "))

            try:
                place_order(
                    engine,
                    email,
                    product_name,
                    quantity
                )
            except ValueError as e:
                print(f"Order failed: {e}")

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
