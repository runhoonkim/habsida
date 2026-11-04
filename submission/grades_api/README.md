# Student Grades API

A REST API built with FastAPI, SQLAlchemy, Pydantic, and PostgreSQL. It manages students, courses, and grades, with request validation, pagination, name filtering, and SQL-based average reports.

## Prerequisites

- Python 3.10 or newer.
- Docker with an existing PostgreSQL container named `pg`, exposed on localhost port `5432`.
- The `student_grades.sql` script from the SQL schema project.

Run the commands below from the `grades_api` project directory. Place `student_grades.sql` there, or adjust its path in the import command.

## 1. Create and load the database

Start the existing PostgreSQL container:

```bash
docker start pg
```

Create a dedicated database and load the schema and sample data:

```bash
docker exec pg psql -U postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE school;"
docker exec -i pg psql -U postgres -d school -v ON_ERROR_STOP=1 < student_grades.sql
```

If `school` already exists, skip the creation command. Load the script once into a fresh database; rerunning it may produce duplicate-table or duplicate-data errors. Any UPDATE and DELETE statements in the script also run during import.

Confirm the tables were created:

```bash
docker exec pg psql -U postgres -d school -c '\dt'
```

Expected tables: `students`, `courses`, and `grades`.

## 2. Configure environment variables

Create `.env` beside `database.py`:

```dotenv
DATABASE_URL=postgresql+psycopg://example_username:example_password@localhost:5432/school
```

`DATABASE_URL` supplies the database driver, username, password, host, port, and database name. Replace `example_password` with your local PostgreSQL password; the value above is only an example. This example uses Psycopg 3, installed below.

Keep local credentials and generated files out of Git by adding these entries to `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
.DS_Store
```

An `.env.example` containing only the placeholder connection string can be committed for other developers.

## 3. Install dependencies

Create and activate a virtual environment on macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

The `requirements.txt` file should contain:

```text
fastapi[standard]
sqlalchemy
psycopg[binary]
python-dotenv
pydantic[email]
pytest
httpx
```

If the file is not present, create it with those entries. Then install:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`pydantic[email]` includes the email-validation dependency required by `EmailStr`.

## 4. Run the server

From the directory containing `main.py`, run:

```bash
fastapi dev main.py
```

Alternatively:

```bash
python -m uvicorn main:app --reload
```

- API base URL: <http://127.0.0.1:8000>
- Interactive Swagger documentation: <http://127.0.0.1:8000/docs>
- ReDoc documentation: <http://127.0.0.1:8000/redoc>

Use `/docs` to create a student and course, record a grade, and inspect the reports. Committed data remains in PostgreSQL after the API server restarts.

## API overview

| Resource | Routes |
| --- | --- |
| Students | `POST /students`, `GET /students`, `GET /students/{student_id}`, `PATCH /students/{student_id}`, `DELETE /students/{student_id}` |
| Courses | `POST /courses`, `GET /courses`, `GET /courses/{course_id}`, `PATCH /courses/{course_id}`, `DELETE /courses/{course_id}` |
| Grades | `POST /grades`, `GET /students/{student_id}/grades`, `PATCH /grades/{grade_id}`, `DELETE /grades/{grade_id}` |
| Reports | `GET /reports/student-averages`, `GET /reports/course-averages` |

Student and course lists support `skip` and `limit`, with a maximum limit of 100. Students can also be filtered by a case-insensitive name substring:

```text
GET /students?name=kim&skip=0&limit=20
```

Credits must be greater than zero, and grades must be between 0 and 100 inclusive. Invalid request data returns `422`; missing resources return `404`; duplicate emails and duplicate student-course grades return `409`. Creating a grade with an unknown student or course returns `400`.

## Student versus course deletion — section 3.5

For this assignment, deleting a student removes that student and all their grades in one transaction. Deleting a course with grades is blocked with `409`; a course without grades can be deleted with `204`.

For a real school, I would archive students and courses rather than permanently delete records with grades, preserving transcripts and academic history. If permanent deletion is allowed, I would block it whenever grades still reference either resource and require an explicit records-retention process.

If student deletion uses a database cascade, apply `ON DELETE CASCADE` only to the student foreign key; keep the course foreign key restrictive. Changing ORM declarations alone does not alter existing database constraints.

## Run acceptance tests

Place the supplied `test_grades_api.py` beside `main.py`, then run:

```bash
python -m pytest -v
```

The tests use FastAPI's `TestClient`, so a separate API server is unnecessary, but PostgreSQL must be running and `.env` must point to the initialized `school` database. The supplied fixtures create and clean up test records through the API; do not modify the acceptance tests.

If the enrollment-date test differs by one day, compare PostgreSQL's session timezone with the Python machine's timezone:

```bash
docker exec pg psql -U postgres -d school -c 'SHOW TIMEZONE; SELECT CURRENT_DATE;'
```

Use a consistent timezone for the API database sessions and the test environment.
