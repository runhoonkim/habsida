"""Acceptance tests for the Student Grades API.

Run from the project folder with `pytest -v`. The tests talk to your app in-process through FastAPI's TestClient (no
server needed) and use the real database from your .env. Every test creates its own uniquely named data and deletes it
afterwards, so your existing rows are untouched.
"""

import uuid
from contextlib import suppress
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from main import app

MISSING_ID = 999_999_999  # an id that never exists


@pytest.fixture(scope='session')
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make(client):
    """Factory for students and courses that cleans up everything it created."""
    student_ids, course_ids = [], []

    def student(**overrides):
        payload = {'full_name': 'Test Student', 'email': f'test-{uuid.uuid4().hex[:12]}@example.com'} | overrides
        resp = client.post('/students', json=payload)
        assert resp.status_code == 201, resp.text
        student_ids.append(resp.json()['student_id'])
        return resp.json()

    def course(**overrides):
        payload = {'course_name': f'Course {uuid.uuid4().hex[:8]}', 'instructor_name': 'Dr. Test', 'credits': 3}
        resp = client.post('/courses', json=payload | overrides)
        assert resp.status_code == 201, resp.text
        course_ids.append(resp.json()['course_id'])
        return resp.json()

    def grade(student_id, course_id, value):
        resp = client.post('/grades', json={'student_id': student_id, 'course_id': course_id, 'grade': value})
        assert resp.status_code == 201, resp.text
        return resp.json()

    yield SimpleNamespace(student=student, course=course, grade=grade)

    # students first: deleting a student also deletes their grades, which unblocks the courses.
    # Cleanup is best effort: if your DELETE endpoints are still broken, the failing test already says so.
    for path in [f'/students/{i}' for i in student_ids] + [f'/courses/{i}' for i in course_ids]:
        with suppress(Exception):
            client.delete(path)


# ---------- Students ----------


def test_create_student(make):
    student = make.student(full_name='Ada Lovelace', birth_date='2001-12-10')
    assert student['full_name'] == 'Ada Lovelace'
    assert student['birth_date'] == '2001-12-10'
    assert student['enrollment_date'] == date.today().isoformat()  # filled in by the database


def test_duplicate_email_is_409(client, make):
    student = make.student()
    resp = client.post('/students', json={'full_name': 'Someone Else', 'email': student['email']})
    assert resp.status_code == 409


@pytest.mark.parametrize(
    'payload',
    [
        {'full_name': 'No Email'},
        {'full_name': 'Bad Email', 'email': 'not-an-email'},
        {'email': 'no-name@example.com'},
        {'full_name': 'Bad Date', 'email': 'bad-date@example.com', 'birth_date': 'yesterday'},
    ],
)
def test_invalid_student_is_422(client, payload):
    assert client.post('/students', json=payload).status_code == 422


def test_get_student(client, make):
    student = make.student()
    resp = client.get(f"/students/{student['student_id']}")
    assert resp.status_code == 200
    assert resp.json() == student


def test_get_missing_student_is_404(client):
    assert client.get(f'/students/{MISSING_ID}').status_code == 404


def test_patch_student_changes_only_sent_fields(client, make):
    student = make.student(full_name='Alan Turing')
    resp = client.patch(f"/students/{student['student_id']}", json={'birth_date': '2000-06-23'})
    assert resp.status_code == 200
    assert resp.json()['birth_date'] == '2000-06-23'
    assert resp.json()['full_name'] == 'Alan Turing'


def test_patch_student_to_taken_email_is_409(client, make):
    first, second = make.student(), make.student()
    resp = client.patch(f"/students/{second['student_id']}", json={'email': first['email']})
    assert resp.status_code == 409


def test_patch_student_keeping_own_email_is_ok(client, make):
    student = make.student()
    resp = client.patch(f"/students/{student['student_id']}", json={'email': student['email']})
    assert resp.status_code == 200


def test_patch_missing_student_is_404(client):
    assert client.patch(f'/students/{MISSING_ID}', json={'full_name': 'Nobody'}).status_code == 404


def test_list_students_pagination(client, make):
    for _ in range(3):
        make.student()
    assert len(client.get('/students', params={'limit': 2}).json()) == 2
    assert client.get('/students', params={'limit': 101}).status_code == 422
    assert client.get('/students', params={'skip': -1}).status_code == 422


def test_list_students_name_filter_is_case_insensitive(client, make):
    tag = uuid.uuid4().hex[:8]
    match = make.student(full_name=f'Grace {tag} Hopper')
    make.student(full_name='Somebody Else')

    found = client.get('/students', params={'name': tag.upper()}).json()
    assert [s['student_id'] for s in found] == [match['student_id']]


def test_delete_student_also_deletes_grades(client, make):
    student, course = make.student(), make.course()
    grade = make.grade(student['student_id'], course['course_id'], 80)

    assert client.delete(f"/students/{student['student_id']}").status_code == 204
    assert client.get(f"/students/{student['student_id']}").status_code == 404
    assert client.delete(f"/grades/{grade['grade_id']}").status_code == 404  # the grade went with the student


def test_delete_missing_student_is_404(client):
    assert client.delete(f'/students/{MISSING_ID}').status_code == 404


# ---------- Courses ----------


def test_create_and_get_course(client, make):
    course = make.course(course_name='Databases', credits=4)
    resp = client.get(f"/courses/{course['course_id']}")
    assert resp.status_code == 200
    assert resp.json()['course_name'] == 'Databases'
    assert resp.json()['credits'] == 4


@pytest.mark.parametrize('credits', [0, -2])
def test_course_credits_must_be_positive(client, credits):
    resp = client.post('/courses', json={'course_name': 'Bad', 'instructor_name': 'Nobody', 'credits': credits})
    assert resp.status_code == 422


def test_patch_course(client, make):
    course = make.course(instructor_name='Dr. Codd')
    resp = client.patch(f"/courses/{course['course_id']}", json={'credits': 5})
    assert resp.status_code == 200
    assert resp.json()['credits'] == 5
    assert resp.json()['instructor_name'] == 'Dr. Codd'


def test_list_courses_pagination(client, make):
    for _ in range(3):
        make.course()
    assert len(client.get('/courses', params={'limit': 2}).json()) == 2
    assert client.get('/courses', params={'limit': 101}).status_code == 422


def test_get_missing_course_is_404(client):
    assert client.get(f'/courses/{MISSING_ID}').status_code == 404


def test_delete_course_with_grades_is_409(client, make):
    student, course = make.student(), make.course()
    make.grade(student['student_id'], course['course_id'], 70)
    assert client.delete(f"/courses/{course['course_id']}").status_code == 409


def test_delete_course_without_grades(client, make):
    course = make.course()
    assert client.delete(f"/courses/{course['course_id']}").status_code == 204
    assert client.get(f"/courses/{course['course_id']}").status_code == 404


# ---------- Grades ----------


def test_create_grade(make):
    student, course = make.student(), make.course()
    grade = make.grade(student['student_id'], course['course_id'], 88.5)
    assert grade['grade'] == 88.5
    assert grade['student_id'] == student['student_id']


def test_grade_for_unknown_student_or_course_is_400(client, make):
    student, course = make.student(), make.course()
    bad_student = {'student_id': MISSING_ID, 'course_id': course['course_id'], 'grade': 50}
    bad_course = {'student_id': student['student_id'], 'course_id': MISSING_ID, 'grade': 50}
    assert client.post('/grades', json=bad_student).status_code == 400
    assert client.post('/grades', json=bad_course).status_code == 400


def test_second_grade_in_same_course_is_409(client, make):
    student, course = make.student(), make.course()
    make.grade(student['student_id'], course['course_id'], 70)
    payload = {'student_id': student['student_id'], 'course_id': course['course_id'], 'grade': 90}
    assert client.post('/grades', json=payload).status_code == 409


@pytest.mark.parametrize('value', [-1, 100.01, 150])
def test_grade_out_of_range_is_422(client, make, value):
    student, course = make.student(), make.course()
    payload = {'student_id': student['student_id'], 'course_id': course['course_id'], 'grade': value}
    assert client.post('/grades', json=payload).status_code == 422


def test_list_student_grades(client, make):
    student, math, science = make.student(), make.course(), make.course()
    make.grade(student['student_id'], math['course_id'], 85)
    make.grade(student['student_id'], science['course_id'], 90)

    grades = client.get(f"/students/{student['student_id']}/grades").json()
    assert sorted(g['grade'] for g in grades) == [85, 90]


def test_grades_of_missing_student_is_404(client):
    assert client.get(f'/students/{MISSING_ID}/grades').status_code == 404


def test_patch_grade(client, make):
    student, course = make.student(), make.course()
    grade = make.grade(student['student_id'], course['course_id'], 85)

    resp = client.patch(f"/grades/{grade['grade_id']}", json={'grade': 92})
    assert resp.status_code == 200
    assert resp.json()['grade'] == 92
    assert client.patch(f"/grades/{grade['grade_id']}", json={'grade': 101}).status_code == 422
    assert client.patch(f'/grades/{MISSING_ID}', json={'grade': 50}).status_code == 404


def test_delete_grade(client, make):
    student, course = make.student(), make.course()
    grade = make.grade(student['student_id'], course['course_id'], 85)

    assert client.delete(f"/grades/{grade['grade_id']}").status_code == 204
    assert client.get(f"/students/{student['student_id']}/grades").json() == []


# ---------- Reports ----------


def test_student_average_after_update(client, make):
    # the same steps as main() in part 2 of the Python project: add, update, display
    alice, math, science = make.student(full_name='Alice'), make.course(), make.course()
    math_grade = make.grade(alice['student_id'], math['course_id'], 85)
    make.grade(alice['student_id'], science['course_id'], 90)
    client.patch(f"/grades/{math_grade['grade_id']}", json={'grade': 92})

    report = client.get('/reports/student-averages').json()
    row = next(r for r in report if r['student_id'] == alice['student_id'])
    assert row['full_name'] == 'Alice'
    assert row['average_grade'] == 91.0
    assert row['courses_taken'] == 2


def test_course_average(client, make):
    course, first, second, third = make.course(), make.student(), make.student(), make.student()
    for student, value in ((first, 70), (second, 80), (third, 95)):
        make.grade(student['student_id'], course['course_id'], value)

    report = client.get('/reports/course-averages').json()
    row = next(r for r in report if r['course_id'] == course['course_id'])
    assert row['course_name'] == course['course_name']
    assert row['average_grade'] == 81.67  # (70 + 80 + 95) / 3, rounded to 2 decimals
    assert row['students_graded'] == 3
