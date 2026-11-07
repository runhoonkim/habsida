from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from database import get_db
from models import Student, Course, Grade
from schemas import (
    StudentCreate, StudentUpdate, StudentOut,    
    CourseCreate, CourseUpdate, CourseOut,
    GradeCreate, GradeUpdate, GradeOut,
    StudentAverageOut, CourseAverageOut
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

app = FastAPI(title="Grades API")

def commit_or_raise(db: Session = Depends(get_db)):
    """
    Raise a HTTPException error before commit if a conflict exists.
    """
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        # exc                          SQLAlchemy IntegrityError
        # └── orig                     Original PostgreSQL driver exception
        #     └── diag                 Diagnostic information
        #         └── constraint_name  Name of the violated constraint
        
        diag = getattr(exc.orig, "diag", None)
        constraint_name = getattr(diag, "constraint_name", None)

        messages = {
            "students_email_key": "Email already exists.",
            "uq_courses_course_name": "Course name already exists.",
            "grades_student_id_course_id_key": "The student already has a grade in this course.",
        }

        if constraint_name in messages:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=messages[constraint_name],
            ) from exc

        raise  # propagate any unrecognized integrity error.


# ===============
# Students CRUD
# ===============
@app.post("/students", response_model=StudentOut, status_code=201)
def create_student(
    payload:StudentCreate, 
    db: Session=Depends(get_db)
):    
    student = Student(**payload.model_dump())
    db.add(student)

    commit_or_raise(db)

    db.refresh(student)     # Reload server-generated fields like id and enrollment_Date
    return student

@app.get("/students", response_model=list[StudentOut], status_code=200)
def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    name: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(Student)
    
    if name is not None:
        query = query.filter(
            Student.full_name.icontains(name, autoescape=True)
        )

    return (
        query
        .order_by(Student.student_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

@app.get("/students/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student

@app.patch("/students/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)
    # Check if student exists
    if student is None:
        raise HTTPException(
            status_code=404, 
            detail="Student not found.",
        )
    
    # ====================================
    # Check if email exists, when supplied
    # ====================================
    changes = payload.model_dump(exclude_unset=True)

    # These database columns cannot be NULL.
    for field in ("full_name", "email"):
        # reject explicit null values
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null.",
            )

    # update student
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)

    commit_or_raise(db)
    
    db.refresh(student)
    return student

@app.delete("/students/{student_id}", status_code=204)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)
    # check if student exists
    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found."
        )
    
    db.query(Grade).filter(Grade.student_id == student_id).delete()
    db.delete(student)
    db.commit()      # PostgreSQL also deletes the student's grades using ondelete="CASCADE".

    return Response(status_code=204)

# ===============
# Courses CRUD
# ===============
@app.post("/courses", response_model=CourseOut, status_code=201)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
):
    course = Course(**payload.model_dump())
    db.add(course)

    commit_or_raise(db)
    
    db.refresh(course)
    return course

@app.get("/courses", response_model=list[CourseOut])
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return (
        db.query(Course)
        .order_by(Course.course_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

@app.get("/courses/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    # check if course exists
    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found."
        )
    return course

@app.patch("/courses/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    # check if course exists
    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found."
        )

    changes = payload.model_dump(exclude_unset=True)

    # reject explicit null values
    for field, value in changes.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null.",
            )

    # update course
    for field, value in changes.items():
        setattr(course, field, value)

    commit_or_raise(db)

    db.refresh(course)
    return course


@app.delete("/courses/{course_id}", status_code=204)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    # check if course exists
    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found."
        )
    
    existing_grade = (
        db.query(Grade)
        .filter(Grade.course_id == course_id)
        .first()
    )

    if existing_grade is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a course that has grades.",
        )
    db.delete(course)
    db.commit()

    return Response(status_code=204)

# ===============
# Grades CRUD
# ===============
@app.post("/grades", response_model=GradeOut, status_code=201)
def create_grade(
    payload: GradeCreate,
    db: Session = Depends(get_db),
):
    # check if student exists
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(
            status_code=400,
            detail="Student not found."
        )
    # check if course exists
    course = db.get(Course, payload.course_id)
    if course is None:
        raise HTTPException(
            status_code=400,
            detail="Course not found."
        )

    # create grade
    grade = Grade(**payload.model_dump())
    db.add(grade)

    commit_or_raise(db)
    
    db.refresh(grade)
    return grade

@app.get("/students/{student_id}/grades", response_model=list[GradeOut])
def list_grades(
    student_id: int,
    db: Session = Depends(get_db),
):
    # check if student exists
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )
    
    # show all grades of the student
    return (
        db.query(Grade)
        .filter(Grade.student_id == student_id)
        .order_by(Grade.grade_id)
        .all()
    )

@app.patch("/grades/{grade_id}", response_model=GradeOut)
def update_grade(
    grade_id: int,
    payload: GradeUpdate,
    db: Session = Depends(get_db),
):
    grade = db.get(Grade, grade_id)

    if grade is None:
        raise HTTPException(
            status_code=404,
            detail="Grade not found.",
        )

    changes = payload.model_dump(exclude_unset=True)

    # reject explicit null
    if "grade" in changes and changes["grade"] is None:
        raise HTTPException(
            status_code=422,
            detail="Grade cannot be null.",
        )

    for field, value in changes.items():
        setattr(grade, field, value)

    db.commit()
    db.refresh(grade)

    return grade

@app.delete("/grades/{grade_id}", status_code=204)
def delete_grade(
    grade_id: int,
    db: Session = Depends(get_db),
):
    grade = db.get(Grade, grade_id)
    if grade is None:
        raise HTTPException(
            status_code=404,
            detail="Grade not found.",
        )

    db.delete(grade)
    db.commit()

    return Response(status_code=204)

@app.get("/reports/student-averages", response_model=list[StudentAverageOut])
def get_student_averages(
    db: Session = Depends(get_db)
):
    return (
        db.query(
            Student.student_id,
            Student.full_name,
            func.round(func.avg(Grade.grade), 2).label("average_grade"),
            func.count(Grade.grade_id).label("courses_taken"),
        )
        .join(Grade, Grade.student_id == Student.student_id)
        .group_by(Student.student_id, Student.full_name)
        .order_by(Student.student_id)
        .all()
    )

@app.get("/reports/course-averages", response_model=list[CourseAverageOut])
def get_course_averages(
    db: Session = Depends(get_db)
):
    return (
        db.query(
            Course.course_id,
            Course.course_name,
            func.round(func.avg(Grade.grade), 2).label("average_grade"),
            func.count(Grade.grade_id).label("students_graded"),
        )
        .join(Grade, Grade.course_id == Course.course_id)
        .group_by(Course.course_id, Course.course_name)
        .order_by(Course.course_id)
        .all()
    )