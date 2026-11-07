from datetime import date
from pydantic import BaseModel, ConfigDict, Field, EmailStr


# =====================================================
# Define pydantic models for Student ORM model
# =====================================================
class StudentCreate(BaseModel):
    full_name: str
    email: EmailStr 
    birth_date: date | None = None

class StudentUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None

class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    full_name: str
    email: EmailStr
    birth_date: date | None
    enrollment_date: date

# =====================================================
# Define pydantic models for Course ORM model
# =====================================================
class CourseCreate(BaseModel):
    course_name: str 
    instructor_name: str 
    credits: int = Field(gt=0)

class CourseUpdate(BaseModel):
    course_name: str | None = None
    instructor_name: str | None = None
    credits: int | None = Field(default=None, gt=0)

class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: int
    course_name: str
    instructor_name: str
    credits: int

# =====================================================
# Define pydantic models for Grade ORM model
# =====================================================
class GradeCreate(BaseModel):
    student_id: int
    course_id: int
    grade: float = Field(ge=0, le=100)

class GradeUpdate(BaseModel):
    grade: float | None = Field(default=None, ge=0, le=100)

class GradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    grade_id: int
    student_id: int
    course_id: int
    grade: float

class StudentGradeOut(GradeOut):
    course_name: str

# =====================================================
# Define pydantic models for average reports
# =====================================================
class StudentAverageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    full_name: str
    average_grade: float | None
    courses_taken: int

class CourseAverageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: int
    course_name: str
    average_grade: float | None
    students_graded: int