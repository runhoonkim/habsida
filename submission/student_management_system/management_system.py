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
            self.students[name] = {"grades": grades}
            return True

    def update_grade(self, name: str, subject: str, grade: int) -> bool:
        """Update a specific student's grade for a given subject."""
            # Return false if student was not found
        if name not in self.students:
            return False

        # Return false if the subject was not found
        if subject not in self.students[name]["grades"]:
            return False

        # else, update the grade and return True
        self.students[name]["grades"][subject] = grade
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
        # =====================================================
        # Print all student records
        # =====================================================
        print(f"All student records:\n{self.students}\n")


        # =====================================================
        # Define helper function for calculating average grades
        # =====================================================

        get_avg = lambda x: round(sum(x) / len(x), 1)

        # =====================================================
        # Print the average grade for each student
        # =====================================================

        # First get a dictionary of list of grades for each student
        grades_per_student = {student: list(student_dict["grades"].values()) for student, student_dict in self.students.items()}

        # Get average for each student from a list of grades and round it to the one decimal place
        avg_per_student = {student: get_avg(grades) for student, grades in grades_per_student.items()}

        print(f"Average grade for each student:\n{avg_per_student}\n")

        # =====================================================
        # Print the average grade for each subject
        # =====================================================
        # Get a list of grades per student first
        list_of_grades_per_student = [student_dict["grades"] for student_dict in self.students.values()]

        # Make a dictionary where keys are subjects and values are lists of grades for each student
        grades_per_subject = {}
        for grades in list_of_grades_per_student:
            for subject, grade in grades.items():
                if subject not in grades_per_subject:
                    grades_per_subject[subject] = []
                grades_per_subject[subject].append(grade)

        # Calculate average for each subject
        avg_per_subject = {subject: get_avg(grades) for subject, grades in grades_per_subject.items()}

        print(f"Average grade for each subject:\n{avg_per_subject}")

    def save_to_file(self, filename: str = "students.json") -> bool:
        """Save all students to a JSON file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.students, f, indent=4)
            return True

        except (TypeError, OverflowError, ValueError, IOError):
            # Catches JSON serialization errors or file system I/O errors
            return False

    def load_from_file(self, filename: str = "students.json") -> bool:
        """Load student data from a JSON file."""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                self.students = json.load(file)
                return True
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            return False