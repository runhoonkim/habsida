/*
Setup
Use the same PostgreSQL container from Lesson 1. You don't need to touch schema.sql or seed.sql — these are brand-new tables, so just connect and create them directly:

docker start pg
docker exec -it pg psql -U postgres
Or run your finished script straight from the file once it's ready:

docker exec -i pg psql -U postgres < student_grades.sql
*/

/*
Requirements
3.1 Design the Schema
No starter code this time — you write every CREATE TABLE statement yourself, choosing the column names, types, and constraints. 
Your schema must satisfy the following requirements:

students
    a primary key that auto-increments;
    a required full name;
    an email that is required and unique across all students;
    a birth date (optional — students may not want to share it);
    an enrollment date that defaults to today if not supplied.

courses
    a primary key that auto-increments;
    a required course name;
    a required instructor name;
    a number of credits that is required and must be greater than 0 (use a CHECK constraint — see the price_non_negative example in the DDL & CRUD lesson).

grades
    a primary key that auto-increments;
    a reference to the student it belongs to, required, and invalid without a matching row in students;
    a reference to the course it belongs to, required, and invalid without a matching row in courses;
    a numeric grade that is required and must fall between 0 and 100 (a CHECK constraint, like the reviews.rating exercise);
    a student can have only one grade per course — no duplicate (student_id, course_id) pairs (a UNIQUE constraint, the same pattern that stopped a user reviewing a product twice).

Hint: "a reference that is invalid without a matching row" is a foreign key 
(REFERENCES students(...), REFERENCES courses(...)) — the exact mechanism orders uses to point at users and products in the course schema. 
Add constraints inline when you write the column (credits INTEGER NOT NULL CHECK (credits > 0)), 
or as a separate line at the end of the CREATE TABLE (UNIQUE (student_id, course_id)) — both are valid, pick whichever reads clearer to you.
*/

-- Create a table students then check the result
CREATE TABLE students (
    student_id SERIAL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    birth_date DATE,
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,

    PRIMARY KEY (student_id)
);

SELECT * FROM students;

-- Create a table courses then check the result
CREATE TABLE courses (
    course_id SERIAL,
    course_name TEXT NOT NULL,
    instructor_name TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0),

    PRIMARY KEY (course_id)
);

SELECT * FROM courses;

-- Create a table grades then check the result
CREATE TABLE grades (
    grade_id SERIAL,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    grade NUMERIC(5, 2) NOT NULL CHECK (grade BETWEEN 0 AND 100),

    PRIMARY KEY (grade_id),
    FOREIGN KEY (student_id)    REFERENCES students(student_id),
    FOREIGN KEY (course_id)     REFERENCES courses(course_id),
    UNIQUE(student_id, course_id)
);

SELECT * FROM grades;

/*
3.2 Populate the Tables
In your script, after the three CREATE TABLE statements:

    INSERT 3 courses of your choice (e.g. 'Databases', 'Statistics', 'Algorithms').
    INSERT 3 students of your choice.
    INSERT at least 4 grades, linking your students to your courses, so that at least one student has grades in more than one course.
*/

-- Populate the table courses and check the result
INSERT INTO courses (course_name, instructor_name, credits) VALUES
    ('Databases', 'Alice Johnson', 3),
    ('Statistics', 'Bob Williams', 3),
    ('Algorithms', 'Charlie Brown', 3);

SELECT * FROM courses;

-- Populate the table students and check the result
INSERT INTO students (full_name, email, birth_date, enrollment_date) VALUES    
    ('Grace Hopper', 'grace.hopper@example.com', '1998-12-09', DEFAULT),
    ('Hannah Lee', 'hannah.lee@example.com', '2000-05-14', DEFAULT),
    ('Ivy Chen', 'ivy.chen@example.com', '1999-08-22', DEFAULT);

SELECT * FROM students;

-- Populate the table grades and check the result

INSERT INTO grades (student_id, course_id, grade) VALUES
    (1, 1, 95.50),
    (1, 3, 88.00),
    (2, 1, 91.00),
    (2, 2, 87.50),
    (3, 2, 93.00),
    (3, 3, 89.50);

SELECT * FROM grades;

/*
3.3 Update Two Students
Write two UPDATE statements against students — for example, correcting an email, or filling in a birth_date that was left NULL. 
Target each one with a WHERE clause on student_id or email, never by position.
*/

UPDATE students
SET enrollment_date = '2026-09-21'
WHERE student_id = 1;

UPDATE students
SET enrollment_date = '2026-09-21'
WHERE student_id = 3;

SELECT * FROM students WHERE student_id IN (1, 3);

/*
3.4 Delete One Student
Pick one of your three students and DELETE them from students.

Careful: if that student has any rows in grades, 
the foreign key will refuse the delete — exactly the referential-integrity protection from this lesson. 
You have two correct ways to handle it, either is acceptable:

    1. Choose a student who has no grades yet, or
    2. DELETE FROM grades WHERE student_id = ... first, then delete the student.

Either way, your script must run start-to-finish without errors.
*/
-- check data in the table `students`
SELECT * FROM students;

-- since all students have grades in our setup, we have to delete the student from the table `grades` first
-- we will delete 'Grace Hopper' with student_id = 1
DELETE FROM grades
WHERE student_id = 1;

DELETE FROM students
WHERE student_id = 1;

-- check data in the table `students` after deletion
SELECT * FROM students;