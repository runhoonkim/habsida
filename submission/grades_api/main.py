from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from database import get_db
from models import Student, Course, Grade
from schemas import (
    StudentCreate, StudentUpdate, StudentOut,    
    CourseCreate, CourseUpdate, CourseOut,
    GradeCreate, GradeUpdate, GradeOut,
    BulkGradeCreate,
    StudentGradeOut,
    StudentAverageOut, CourseAverageOut
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

app = FastAPI(title="Grades API")

def commit_or_raise(db: Session = Depends(get_db)):
    """
    Commit pending changes and translate recognized constraint violations.

    Args:
        db: Database session passed by the caller.

    Returns:
        None after a successful commit.

    Raises:
        HTTPException: With status 409 for a mapped uniqueness constraint.
        IntegrityError: For an unrecognized integrity violation.

    Any caught IntegrityError triggers rollback before it is translated or
    re-raised. Constraint names must match those in the actual database.
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


# ============================================================
# Students CRUD
# ============================================================
@app.post("/students", response_model=StudentOut, status_code=201,
    description=(
        'Create a student using a full name, unique email, and optional birth date. '
        "Enrollment date defaults to the database's current date. Returns **201** with the "
        'created student, **409** for an email conflict recognized by the constraint '
        'handler, and **422** for invalid input.'
    ),
)
def create_student(
    payload:StudentCreate, 
    db: Session=Depends(get_db)
):    
    """
    Create a student with a unique email address.

    Args:
        payload: Validated request data supplied in the JSON body.
        db: Database session supplied by get_db.

    Returns:
        The created student serialized as StudentOut with status 201.

    Raises:
        HTTPException: With status 409 for a recognized email uniqueness violation.
    """
    student = Student(**payload.model_dump())
    db.add(student)

    commit_or_raise(db)

    db.refresh(student)     # Reload server-generated fields like id and enrollment_Date
    return student

@app.get("/students", response_model=list[StudentOut], status_code=200,
    description=(
        'List students ordered by student ID. Use `skip` (default 0) and `limit` (default '
        '20, maximum 100) for pagination. The optional `name` filter performs a '
        'case-insensitive substring match and treats wildcard characters literally. Returns '
        'an empty list when nothing matches and **422** for invalid query parameters.'
    ),
)
def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    name: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    List students with pagination and an optional name filter.

    Args:
        skip: Number of matching rows to skip; must be nonnegative.
        limit: Maximum rows to return, from 1 to 100; defaults to 20.
        name: Optional case-insensitive literal substring of the full name.
        db: Database session supplied by get_db.

    Returns:
        Matching StudentOut records ordered by student_id, or an empty list.
    """
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

@app.get("/students/{student_id}", response_model=StudentOut,
    description=(
        'Retrieve one student by `student_id`. Returns **404** if the student does not exist '
        'and **422** if the path parameter is invalid.'
    ),
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a student by primary key.

    Args:
        student_id: Primary key of the student.
        db: Database session supplied by get_db.

    Returns:
        The requested student serialized as StudentOut.

    Raises:
        HTTPException: With status 404 if the student does not exist.
    """
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student

@app.patch("/students/{student_id}", response_model=StudentOut,
    description=(
        'Update only the supplied student fields. Omitted fields retain their values. '
        '`birth_date` can be cleared with null; `full_name` and `email` cannot be null. '
        'Returns the updated student, **404** if missing, **409** for a recognized '
        'duplicate-email conflict, and **422** for invalid input or disallowed null values.'
    ),
)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
):
    """
    Partially update a student using explicitly supplied fields.

    Args:
        student_id: Primary key of the student.
        payload: Validated request data supplied in the JSON body.
        db: Database session supplied by get_db.

    Returns:
        The updated student serialized as StudentOut.

    Raises:
        HTTPException: With status 404 if missing, 409 for a recognized email conflict, or 422 for a null full_name or email.
    """
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

@app.delete("/students/{student_id}", status_code=204,
    description=(
        'Delete a student and all of their grades. Returns **204** with no response body, '
        '**404** if the student does not exist, and **422** for an invalid path parameter.'
    ),
)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a student and their associated grades in one transaction.

    Args:
        student_id: Primary key of the student.
        db: Database session supplied by get_db.

    Returns:
        An empty response with status 204 after deletion is committed.

    Raises:
        HTTPException: With status 404 if the student does not exist.
    """
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

# ============================================================
# Courses CRUD
# ============================================================
@app.post("/courses", response_model=CourseOut, status_code=201,
    description=(
        'Create a course with a course name, instructor name, and positive credit count. '
        'Returns **201** with the course, **409** for a course-name conflict recognized by '
        'the constraint handler, and **422** for invalid input.'
    ),
)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
):
    """
    Create a course with a unique name.

    Args:
        payload: Validated request data supplied in the JSON body.
        db: Database session supplied by get_db.

    Returns:
        The created course serialized as CourseOut with status 201.

    Raises:
        HTTPException: With status 409 for a recognized course-name uniqueness violation.
    """
    course = Course(**payload.model_dump())
    db.add(course)

    commit_or_raise(db)
    
    db.refresh(course)
    return course

@app.get("/courses", response_model=list[CourseOut],
    description=(
        'List courses ordered by course ID. Use `skip` (default 0) and `limit` (default 20, '
        'maximum 100) for pagination. Returns an empty list if the page has no courses and '
        '**422** for invalid query parameters.'
    ),
)
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List courses ordered by ID with pagination.

    Args:
        skip: Number of matching rows to skip; must be nonnegative.
        limit: Maximum rows to return, from 1 to 100; defaults to 20.
        db: Database session supplied by get_db.

    Returns:
        CourseOut records ordered by course_id, or an empty list.
    """
    return (
        db.query(Course)
        .order_by(Course.course_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

@app.get("/courses/{course_id}", response_model=CourseOut,
    description=(
        'Retrieve one course by `course_id`. Returns **404** if the course does not exist '
        'and **422** for an invalid path parameter.'
    ),
)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a course by primary key.

    Args:
        course_id: Primary key of the course.
        db: Database session supplied by get_db.

    Returns:
        The requested course serialized as CourseOut.

    Raises:
        HTTPException: With status 404 if the course does not exist.
    """
    course = db.get(Course, course_id)
    # check if course exists
    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found."
        )
    return course

@app.patch("/courses/{course_id}", response_model=CourseOut,
    description=(
        'Update the supplied course fields while retaining omitted values. Explicit null '
        'values are rejected; credits must remain positive. Returns the updated course, '
        '**404** if missing, **409** for a recognized duplicate-name conflict, and **422** '
        'for invalid input.'
    ),
)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
):
    """
    Partially update a course without changing omitted fields.

    Args:
        course_id: Primary key of the course.
        payload: Validated request data supplied in the JSON body.
        db: Database session supplied by get_db.

    Returns:
        The updated course serialized as CourseOut.

    Raises:
        HTTPException: With status 404 if missing, 409 for a recognized name conflict, or 422 for a supplied null value.
    """
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


@app.delete("/courses/{course_id}", status_code=204,
    description=(
        'Delete a course that has no grades. Returns **204** with no response body, **404** '
        'if the course does not exist, **409** if it has grades, and **422** for an invalid '
        'path parameter.'
    ),
)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a course only when it has no associated grades.

    Args:
        course_id: Primary key of the course.
        db: Database session supplied by get_db.

    Returns:
        An empty response with status 204 after deletion is committed.

    Raises:
        HTTPException: With status 404 if missing or 409 if grades reference the course.
    """
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

# ============================================================
# Grades CRUD
# ============================================================
@app.post("/grades", response_model=GradeOut, status_code=201,
    description=(
        'Create a grade from 0 to 100 using a student ID and course ID. Only one grade may '
        'exist for each student/course pair. Returns **201** with the grade, **400** if the '
        'student or course is missing, **409** for a duplicate pair recognized by the '
        'constraint handler, and **422** for invalid input.'
    ),
)
def create_grade(
    payload: GradeCreate,
    db: Session = Depends(get_db),
):
    # check if student exists
    """
    Create one grade for an existing student and course.

    Args:
        payload: Validated request data supplied in the JSON body.
        db: Database session supplied by get_db.

    Returns:
        The created grade serialized as GradeOut with status 201.

    Raises:
        HTTPException: With status 400 if a referenced student or course is missing, or 409 for a recognized duplicate student/course pair.
    """
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

# Bulk create
@app.post(
    "/students/{student_id}/grades", 
    response_model=list[GradeOut],
    status_code=201,
    description=(
        'Submit a nonempty JSON list of objects containing `course_id` and `grade`. Each '
        'course ID must appear only once, and each grade must be from 0 to 100. Intended '
        'success response: **201** with the created grades in request order. Inserts share '
        'one commit; a recognized duplicate-grade constraint violation rolls back the batch '
        'and returns **409**. Missing students or courses are intended to return **404**; '
        'empty or invalid input returns **422**, and repeated course IDs return **409**.'
    ),
)
def create_student_grades(
    student_id: int,
    payload: list[BulkGradeCreate],
    db: Session = Depends(get_db),
): 
    # check if student exists
    """
    Create multiple grades for one student in a single transaction.

    Args:
        student_id: Primary key of the student.
        payload: Validated request data supplied in the JSON body.
        db: Database session supplied by get_db.

    Returns:
        The created GradeOut records in request order with status 201.

    Raises:
        HTTPException: With status 404 for a missing student or the course-missing branch, 422 for an empty list, or 409 for repeated courses or a recognized duplicate grade.
            TypeError: The current course-existence check subtracts a list from a set; fix this before using the endpoint.
    """
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )
    # reject an empty list
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one grade must be provided.",
        )

    # reject repeated course IDs within the request
    course_ids = [item.course_id for item in payload]
    if len(course_ids) != len(set(course_ids)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Each course_id must appear only once in the request."
        )

    # check if every course exists
    existing_courses = (
        db.query(Course)
        .filter(Course.course_id.in_(course_ids))
        .all()
    )

    existing_ids = [course.course_id for course in existing_courses]
    missing_ids = set(course_ids) - existing_ids
    if not missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course(s) not found."
        )

    # create grades
    grades = [
        Grade(
            student_id=student_id,
            course_id=item.course_id,
            grade=item.grade,
        )
        for item in payload
    ]

    db.add_all(grades)
    commit_or_raise(db)

    for grade in grades:
        db.refresh(grade)

    return grades



@app.get("/students/{student_id}/grades", response_model=list[StudentGradeOut],
    description=(
        'List all grades for one student, ordered by grade ID. Each result includes '
        '`course_name` alongside the grade fields, so no separate course lookup is needed. '
        'Returns an empty list for a student without grades, **404** if the student does not '
        'exist, and **422** for an invalid path parameter.'
    ),
)
def list_grades(
    student_id: int,
    db: Session = Depends(get_db),
):
    # check if student exists
    """
    List a student's grades together with course names.

    Args:
        student_id: Primary key of the student.
        db: Database session supplied by get_db.

    Returns:
        StudentGradeOut records containing grade fields and course_name, ordered by
        grade_id.

    Raises:
        HTTPException: With status 404 if the student does not exist.
    """
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )
    
    # show all grades of the student
    return (
        db.query(
            Grade.grade_id,
            Grade.student_id,
            Grade.course_id,
            Grade.grade,
            Course.course_name,
        )
        .join(Course, Grade.course_id == Course.course_id)
        .filter(Grade.student_id == student_id)
        .order_by(Grade.grade_id)
        .all()
    )

@app.patch("/grades/{grade_id}", response_model=GradeOut,
    description=(
        'Update an existing grade using the fields defined by `GradeUpdate`. Omitted fields '
        'retain their values; an explicitly null grade is rejected. Grades must remain from '
        '0 to 100. Returns the updated grade, **404** if it does not exist, and **422** for '
        'invalid input.'
    ),
)
def update_grade(
    grade_id: int,
    payload: GradeUpdate,
    db: Session = Depends(get_db),
):
    """
    Partially update an existing grade.

    Args:
        grade_id: Primary key of the grade.
        payload: Validated request data supplied in the JSON body.
        db: Database session supplied by get_db.

    Returns:
        The updated grade serialized as GradeOut.

    Raises:
        HTTPException: With status 404 if missing or 422 if grade is explicitly null.
    """
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

@app.delete("/grades/{grade_id}", status_code=204,
    description=(
        'Delete one grade by `grade_id`. Returns **204** with no response body after '
        'deletion, **404** if the grade does not exist, and **422** for an invalid path '
        'parameter.'
    ),
)
def delete_grade(
    grade_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a grade by primary key.

    Args:
        grade_id: Primary key of the grade.
        db: Database session supplied by get_db.

    Returns:
        An empty response with status 204 after deletion is committed.

    Raises:
        HTTPException: With status 404 if the grade does not exist.
    """
    grade = db.get(Grade, grade_id)
    if grade is None:
        raise HTTPException(
            status_code=404,
            detail="Grade not found.",
        )

    db.delete(grade)
    db.commit()

    return Response(status_code=204)

# ============================================================
# Reports
# ============================================================
@app.get("/reports/student-averages", response_model=list[StudentAverageOut],
    description=(
        'List students who have grades, ordered by student ID. Each result includes the '
        'student name, average grade rounded to two decimal places, and number of courses '
        'taken. Optionally supply `min_average` from 0 to 100 to include only students whose '
        '**unrounded** average is at least that value. Students without grades are excluded. '
        'Returns an empty list if nothing matches and **422** for an invalid threshold.'
    ),
)
def get_student_averages(
    min_average: float | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """
    Report average grades and course counts for students with grades.

    Args:
        min_average: Optional inclusive minimum average from 0 to 100.
        db: Database session supplied by get_db.

    Returns:
        StudentAverageOut summaries ordered by student_id. Filtering uses the
        unrounded average; displayed averages are rounded to two decimal places.
    """
    average = func.avg(Grade.grade)
    
    query = (
        db.query(
            Student.student_id,
            Student.full_name,
            func.round(average, 2).label("average_grade"),
            func.count(Grade.grade_id).label("courses_taken"),
        )
        .join(Grade, Grade.student_id == Student.student_id)
        .group_by(Student.student_id, Student.full_name)
    )

    # filter by min_average if given
    if min_average is not None:
        query = query.having(average >= min_average)

    return (
        query
        .order_by(Student.student_id)
        .all()
    )


@app.get("/reports/course-averages", response_model=list[CourseAverageOut],
    description=(
        'List courses that have grades, ordered by course ID. Each result includes the '
        'course name, average grade rounded to two decimal places, and number of students '
        'graded. Courses without grades are excluded. Returns an empty list when no courses '
        'have grades.'
    ),
)
def get_course_averages(
    db: Session = Depends(get_db)
):
    """
    Report average grades and student counts for courses with grades.

    Args:
        db: Database session supplied by get_db.

    Returns:
        CourseAverageOut summaries ordered by course_id with rounded average_grade
        and students_graded.
    """
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