# student_management_system/management_system.py

import json
from typing import Dict, List
from student import Student

class StudentManagementSystem:
    def __init__(self):
        """Initialize the student management system with an empty dictionary of students."""
        self.students = {}

    def add_student(self, name: str, grades: Dict[str, int]) -> bool:
        """Add a new student to the system."""
            # if the student already exists, return False
        if name in self.students:
            return False

        # if grades are not in the correct format, return False
        if not isinstance(grades, dict):
            return False

        # if subject and grade are not in the correct format, return False
        for subject, grade in grades.items():
            if not isinstance(subject, str) or not isinstance(grade, int):
                return False

        # else, add students and return True
        else:
            self.students[name] = Student(name, grades)
            return True

    def update_grade(self, name: str, subject: str, grade: int) -> bool:
        """Update a specific student's grade for a given subject."""
            # Return false if student was not found
        if name not in self.students:
            return False

        # Return false if the subject was not found
        if subject not in self.students[name].grades:
            return False

        # else, update the grade and return True
        self.students[name].add_grade(subject, grade)
        return True

    def delete_student(self, name: str) -> bool:
        """Delete a student from the system."""
            # Reutrn false if the student was not found
        if name not in self.students:
            return False

        # else, delete student and return true
        del self.students[name]

        return True

    def display_records(self) -> None:
        """Display all student records with their grades and average grades."""
        if not self.students:
            print("No student records found.")
            return


        # Make a dictionary where keys are subjects and values are lists of grades for each student
        grades_per_subject = {}

        # Display a student's record and their average grades
        for student in self.students.values():
            print(f"Name: {student.name}")
            print(f"Grades: {student.grades}")
            print(f"Average: {student.get_average_grade():.2f}")
            print("-" * 30)

            for subject, grade in student.grades.items():
                if subject not in grades_per_subject:
                    grades_per_subject[subject] = []
                grades_per_subject[subject].append(grade)



        # Define helper function for calculating average grades
        get_avg = lambda x: round(sum(x) / len(x), 1)

        # Calculate average for each subject
        avg_per_subject = {subject: get_avg(grades) for subject, grades in grades_per_subject.items()}

        print(f"Average grade for each subject:\n{avg_per_subject}")




    def save_to_file(self, filename: str = "students.json") -> bool:
        """Save all students to a JSON file."""
        try:
            data = {}

            for student in self.students.values():
                data.update(student.to_dict())

            with open(filename, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)

            return True

        except (OSError, TypeError):
            return False

    def load_from_file(self, filename: str = "students.json") -> bool:
        """Load student data from a JSON file."""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)

            self.students = {}

            for student_data in data.values():
                # Student.from_dict() expects {name: {"grades": ...}}
                # so we need to pass each student entry back in that format.
                pass

            for name, student_data in data.items():
                self.students[name] = Student(
                    name,
                    student_data["grades"]
                )

            return True

        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            return False