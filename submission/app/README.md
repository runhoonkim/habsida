# Orders API

A FastAPI service for user registration, JWT authentication, and order management. Built with PostgreSQL, SQLAlchemy, and Pydantic v2, with ownership checks and admin-only order deletion.

## Setup

1. Load the course database using `schema.sql`, followed by `seed.sql`. The database must contain the `users`, `products`, and `orders` tables.

2. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install "fastapi[standard]" sqlalchemy "psycopg[binary]" python-dotenv "pydantic[email]" "python-jose[cryptography]" "passlib[bcrypt]==1.7.4" "bcrypt==4.0.1" httpx
   ```

   The Passlib/bcrypt versions match this project's existing hashing setup. If a `requirements.txt` is provided, install it with `python -m pip install -r requirements.txt` instead.

3. Create `app/.env` with your local settings. These values are examples only:

   ```dotenv
   DATABASE_URL=postgresql+psycopg://postgres:example_password@localhost:5432/store
   SECRET_KEY=replace_with_a_generated_random_secret
   ALGORITHM=HS256
   ```

   Replace the database name and credentials as needed. Generate a signing secret with:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Keep `.env` and `.venv/` out of Git.

## Run

From the project root containing `app/`:

```bash
fastapi dev app/main.py
```

Open [Swagger UI](http://127.0.0.1:8000/docs). Click **Authorize** and enter an email in the `username` field plus its password. The supplied seed users, such as `user1@example.com`, use `password123`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/register` | Register a user with a hashed password; duplicate email returns `409` |
| POST | `/token` | Exchange form credentials for a JWT; invalid credentials return `401` |
| GET | `/me` | Read the authenticated user's public information |
| POST | `/orders` | Create an order for the current user; unknown product returns `400` |
| GET | `/orders` | List accessible orders with `skip`, `limit` (maximum 100), `status`, and `product_id` filters |
| GET | `/orders/{id}` | Read an order; missing returns `404`, unauthorized access returns `403` |
| PATCH | `/orders/{id}` | Partially update an order with the same ownership checks |
| DELETE | `/orders/{id}` | Delete an order as an admin; returns `204` |
| GET | `/products` | List products as any authenticated user |
| GET | `/products/{id}` | Read a product as any authenticated user |

Regular users access their own orders; admins can list all orders. Protected requests send `Authorization: Bearer <access_token>`. Request validation errors return `422`, and response schemas exclude password fields.

## Demonstration

Use `/docs` or an HTTPX script/Postman collection to register, log in, create an order using an existing product ID, and retrieve or update it. Verify that another regular user cannot access the order and that only an admin can delete it.
