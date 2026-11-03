from fastapi import Depends, FastAPI, HTTPException, Query, Response
from database import get_db
from models import Student, Course, Grade
from schemas import (
    StudentCreate, StudentUpdate, StudentOut,    
    CourseCreate, CourseUpdate, CourseOut,
    GradeCreate, GradeUpdate, GradeOut
)
from sqlalchemy.orm import Session

app = FastAPI(title="Grades API")

# ===============
# Students CRUD
# ===============
@app.post("/students", response_model=StudentOut, status_code=201)
def create_student(
    payload:StudentCreate, 
    db: Session=Depends(get_db)
):
    # check if email already exists
    existing_email = (
        db.query(Student)
        .filter(Student.email == payload.email)
        .first()
    )

    if existing_email is not None:
        raise HTTPException(
            status_code=409,
            detail="Email already exists.",
        )
    
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
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
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null.",
            )

    # Check only a supplied email, excluding this student's own row.
    if "email" in changes:
        existing_student = (
            db.query(Student)
            .filter(
                Student.email == changes["email"],
                Student.student_id != student_id,
            )
            .first()
        )

        if existing_student is not None:
            raise HTTPException(
                status_code=409,
                detail="Email already exists.",
            )

    # Update student
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)

    db.commit()
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
    db.commit()
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

    for field, value in changes.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null.",
            )

    changes = payload.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(course, field, value)

    db.commit()
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
    
    db.delete(course)
    db.commit()

    return Response(status_code=204)

# ===============
# Grades CRUD
# ===============
@app.post("/grades", response_model=GradeOut, status_code=201)
def create_grade(
    
):
    pass