import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import User, Product

# Load environment variables from .env file
load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

# Delete product by name
with Session(engine) as session:
    product = session.scalars(
        select(Product)
        .where(Product.name == "SQLAlchemy Demo Product")
        .order_by(Product.id.desc())
    ).first()

    if product is None:
        print("Product not found.")

    else:
        product_id = product.id
        session.delete(product)
        session.commit()
        print("Product deleted with ID:", product_id)

# Test result
with Session(engine) as session:
    products = session.scalars(
        select(Product)
        .where(Product.name == "SQLAlchemy Demo Product")
    ).all()

    if products:
        for product in products:
            print(product.name, ":", product.price, ":", product.stock)
    else:
        print("No products found.")

# Update product stock quantity
# with Session(engine) as session:
#     product = session.scalars(
#         select(Product)
#         .where(Product.name == "SQLAlchemy Demo Product")
#         .order_by(Product.id.desc())
#     ).first()

#     if product is None:
#         print("Product not found.")

#     else:
#         product.stock += 10
#         session.commit()
#         print(product.name, "new stock:", product.stock)

# Example 3
# with Session(engine) as session:
#     product = Product(
#         name = "SQLAlchemy Demo Product",
#         category = "Office",
#         description = "Created from Python using SQLAlchemy",
#         price = 34.95,
#         stock = 80,
#     )

#     session.add(product)
#     session.commit()
#     print("New product added with ID:", product.id)

# Check the result
# with Session(engine) as session:
#     products = session.scalars(
#         select(Product)
#         .order_by(Product.id.desc())
#     ).first()

#     if products:
#         print(products.name, ":", products.price, ":", products.stock)
#     else:
#         print("No products found.")

# Example 2
# with Session(engine) as session:
#     admins = session.scalars(
#         select(User).where(User.role == "admin")
#     ).all()

#     for user in admins:
#         print(user.email, ":", user.role)

# Example 1
# selected_role = "admin"

# with engine.connect() as conn:
#     result = conn.execute(
#         text("SELECT email, role FROM users WHERE role = :role"),
#         {"role": selected_role}
#     )

#     for row in result:
#         print(row.email, ":", row.role)