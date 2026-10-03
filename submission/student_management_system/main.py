# student_management_system/main.py

from management_system import StudentManagementSystem

def main():
    system = StudentManagementSystem()

    # Load existing data if available
    system.load_from_file()

    # Example operations
    system.add_student("Alice", {"Math": 85, "Science": 90})
    system.add_student("Bob", {"English": 78, "History": 82})

    system.update_grade("Alice", "Math", 92)
    system.update_grade("Bob", "History", 88)

    system.display_records()

    system.delete_student("Bob")

    # Save data
    system.save_to_file()

if __name__ == "__main__":
    main()