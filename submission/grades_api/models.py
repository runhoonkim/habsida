from datetime import date
from decimal import Decimal
from sqlalchemy import (
    Date, 
    Integer, 
    Numeric, 
    Text, 
    ForeignKey, 
    func, 
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

# =====================================================
# Define Student ORM Model with reference to sql query
# =====================================================
"""
query : 

CREATE TABLE students (
    student_id SERIAL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    birth_date DATE,
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,

    PRIMARY KEY (student_id)
);
"""

class Student(Base):
    __tablename__ = "students"

    # Mapped[...] describes the Python attribute’s type, while mapped_column(...) defines its database column.
    student_id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True,
    )
    full_name: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        Text, 
        unique=True, 
        nullable=False,
    )
    birth_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    enrollment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
    )


# =====================================================
# Define Course ORM Model with reference to sql query
# =====================================================

"""
query : 

CREATE TABLE courses (
    course_id SERIAL,
    course_name TEXT NOT NULL,
    instructor_name TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0),

    PRIMARY KEY (course_id)
);
"""

class Course(Base):
    __tablename__ = "courses"

    __table_args__ = (
        UniqueConstraint(
            "course_name",
            name="uq_courses_course_name",
        )
    )

    course_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    course_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    instructor_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    credits: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("credits > 0"),
        nullable=False,
    )

# =====================================================
# Define Grade ORM Model with reference to sql query
# =====================================================

"""
query : 

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
"""
class Grade(Base):
    __tablename__ = "grades"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            name="uq_grades_student_course",
        ),
    )

    grade_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey(
            "students.student_id", 
            ondelete="CASCADE"
        ),
        nullable=False,
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey(
            "courses.course_id",
        ),
        nullable=False,
    )
    grade: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        CheckConstraint("grade BETWEEN 0 AND 100"),
        nullable=False,
    )