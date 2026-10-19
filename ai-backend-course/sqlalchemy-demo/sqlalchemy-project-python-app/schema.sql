-- =============================================================================
-- shared course database  —  SCHEMA
-- =============================================================================
-- A small online-store backend used across the whole AI Backend track:
--   the SQL chapter  designs and queries it (SQL)
--   the API chapter  serves it through a FastAPI REST API (with auth on `users`)
--   the deployment chapter  containerizes and deploys it
--   the LLM chapter  fills `documents.embedding` and runs RAG over it (pgvector)
--
-- Run this file ONCE to create the structure, then run `seed.sql` to populate it:
--   docker exec -i pg psql -U postgres < schema.sql
--   docker exec -i pg psql -U postgres < seed.sql
-- =============================================================================

-- The pgvector extension ships with the pgvector/pgvector image. We need it for
-- the `documents.embedding` column used in the AI chapters.
CREATE EXTENSION IF NOT EXISTS vector;

-- Start from a clean slate so the file is safe to re-run during the course.
DROP TABLE IF EXISTS orders, documents, products, users CASCADE;

-- -----------------------------------------------------------------------------
-- users — accounts, ready for authentication (the API chapter)
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    email           TEXT        NOT NULL UNIQUE,
    hashed_password TEXT        NOT NULL,
    full_name       TEXT        NOT NULL,
    role            TEXT        NOT NULL DEFAULT 'member'
                                CHECK (role IN ('customer', 'member', 'admin')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- products — the catalog of things for sale
-- -----------------------------------------------------------------------------
CREATE TABLE products (
    id          SERIAL         PRIMARY KEY,
    name        TEXT           NOT NULL,
    category    TEXT           NOT NULL,
    description TEXT,
    price       NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    stock       INTEGER        NOT NULL DEFAULT 0 CHECK (stock >= 0),
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- orders — each purchase links a user to a product they bought
-- -----------------------------------------------------------------------------
CREATE TABLE orders (
    id         SERIAL      PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER     NOT NULL REFERENCES products(id),
    quantity   INTEGER     NOT NULL DEFAULT 1 CHECK (quantity > 0),
    status     TEXT        NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending', 'paid', 'shipped',
                                             'delivered', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- documents — text corpus with an embedding column for retrieval (the LLM chapter)
-- The embedding stays NULL until an embedding model fills it in the AI chapter.
-- 1536 matches OpenAI `text-embedding-3-small`, used later in the course.
-- -----------------------------------------------------------------------------
CREATE TABLE documents (
    id         SERIAL       PRIMARY KEY,
    title      TEXT         NOT NULL,
    content    TEXT         NOT NULL,
    source     TEXT,
    metadata   JSONB        NOT NULL DEFAULT '{}'::jsonb,
    embedding  VECTOR(1536),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- Indexes for the queries students run most often (joins, filters, sorting).
-- -----------------------------------------------------------------------------
CREATE INDEX idx_orders_user_id    ON orders(user_id);
CREATE INDEX idx_orders_product_id ON orders(product_id);
CREATE INDEX idx_orders_status     ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_products_category ON products(category);

-- NOTE: the approximate-nearest-neighbour (HNSW) index on documents.embedding
-- is created in the LLM chapter, AFTER the column has been populated with real
-- embeddings. It is intentionally omitted here.
