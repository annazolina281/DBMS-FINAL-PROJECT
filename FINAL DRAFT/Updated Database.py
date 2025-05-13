import sys
import pyodbc
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QMessageBox, QStackedWidget

# SQL Server connection setup
def create_database():
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=DESKTOP-PSJGEEF;'
        r'DATABASE=master;'
        r'UID=admin;'
        r'PWD=1234;'
    )
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        cursor.execute("""
        IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'CommunityHoursDB')
        BEGIN
            CREATE DATABASE CommunityHoursDB
        END
        """)
        cursor.close()
        conn.close()
        return conn
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None

def connect_to_community_db():
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=DESKTOP-PSJGEEF;'
        r'DATABASE=CommunityHoursDB;'
        r'UID=admin;'
        r'PWD=1234'
    )
    try:
        return pyodbc.connect(conn_str, autocommit=True)
    except Exception as e:
        print(f"❌ Failed to connect to CommunityHoursDB: {e}")
        return None

    
def create_tables():
    conn = connect_to_community_db()
    if conn:
        cursor = conn.cursor()

        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'counselors')
        BEGIN
            CREATE TABLE counselors (
                counselor_id VARCHAR(20) PRIMARY KEY,
                department_1 VARCHAR(10),
                department_2 VARCHAR(10),
                password VARCHAR(50)
            )
        END
        """)

        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'students')
        BEGIN
            CREATE TABLE students (
                student_num INT PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                program VARCHAR(50)
            )
        END
        """)

        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'violations')
        BEGIN
            CREATE TABLE violations (
                violation_id INT PRIMARY KEY IDENTITY(1,1),
                violation_name VARCHAR(100),
                community_hours INT
            )
        END
        """)

        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'student_violations')
        BEGIN
            CREATE TABLE student_violations (
                sv_id INT PRIMARY KEY IDENTITY(1,1),
                student_number INT FOREIGN KEY REFERENCES students(student_num),
                first_offense_id INT FOREIGN KEY REFERENCES violations(violation_id),
                second_offense_id INT FOREIGN KEY REFERENCES violations(violation_id),
                third_offense_id INT FOREIGN KEY REFERENCES violations(violation_id)
            )
        END
        """)

        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'csh')
        BEGIN
            CREATE TABLE csh (
                sv_id INT FOREIGN KEY REFERENCES student_violations(sv_id),
                time_in DATETIME,
                time_out DATETIME,
                counselor_id VARCHAR(20) FOREIGN KEY REFERENCES counselors(counselor_id),
                remarks TEXT
            )
        END
        """)

        conn.commit()
        conn.close()


# Base Window
class RoleSelection(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        create_database()
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select Role:"))

        student_btn = QPushButton("Student")
        counselor_btn = QPushButton("Counselor")
        admin_btn = QPushButton("Admin")

        student_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(1))
        counselor_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(2))
        admin_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(3))

        layout.addWidget(student_btn)
        layout.addWidget(counselor_btn)
        layout.addWidget(admin_btn)
        self.setLayout(layout)

# Student Page
class StudentPage(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        layout = QVBoxLayout()

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter Student Number")
        submit_btn = QPushButton("Submit")
        back_btn = QPushButton("Back")

        submit_btn.clicked.connect(self.login)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        layout.addWidget(QLabel("Student Login"))
        layout.addWidget(self.id_input)
        layout.addWidget(submit_btn)
        layout.addWidget(back_btn)
        self.setLayout(layout)

    def login(self):
        student_id = self.id_input.text()
        conn = connect_to_community_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE student_num = ?", student_id)
            result = cursor.fetchone()
            if result:
                QMessageBox.information(self, "Success", "Student logged in successfully!")
            else:
                QMessageBox.warning(self, "Failed", "Invalid student number.")
            conn.close()

# Counselor Page
class CounselorPage(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        layout = QVBoxLayout()

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter Counselor ID")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Enter Password")
        self.pass_input.setEchoMode(QLineEdit.Password)

        submit_btn = QPushButton("Login")
        back_btn = QPushButton("Back")

        submit_btn.clicked.connect(self.login)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        layout.addWidget(QLabel("Counselor Login"))
        layout.addWidget(self.id_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(submit_btn)
        layout.addWidget(back_btn)
        self.setLayout(layout)

    def login(self):
        counselor_id = self.id_input.text()
        password = self.pass_input.text()
        conn = connect_to_community_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM counselors WHERE counselor_id = ? AND password = ?", (counselor_id, password))
            result = cursor.fetchone()
            if result:
                QMessageBox.information(self, "Success", "Counselor logged in successfully!")
            else:
                QMessageBox.warning(self, "Failed", "Invalid credentials.")
            conn.close()

# Admin Page
class AdminPage(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        layout = QVBoxLayout()

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter Admin ID")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Enter Password")
        self.pass_input.setEchoMode(QLineEdit.Password)

        submit_btn = QPushButton("Login")
        back_btn = QPushButton("Back")

        submit_btn.clicked.connect(self.login)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        layout.addWidget(QLabel("Admin Login"))
        layout.addWidget(self.id_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(submit_btn)
        layout.addWidget(back_btn)
        self.setLayout(layout)

    def login(self):
        admin_id = self.id_input.text()
        admin_pass = self.pass_input.text()
        if admin_id == "admin" and admin_pass == "1234":
            self.stacked_widget.setCurrentIndex(4)
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect ID or password.")

class AdminMenu(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        
        layout = QVBoxLayout()

        student_records_btn = QPushButton("Edit Student Records")
        counselor_records_btn = QPushButton("Edit Counselor Records")
        violations_records_btn = QPushButton("Edit Violation Records")
        csh_records_btn = QPushButton("Edit Community Hours Record")
        back_btn = QPushButton("Back")
        

        student_records_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(5))
        counselor_records_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(6))
        violations_records_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(7))
        csh_records_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(8))
        back_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
        layout.addWidget(student_records_btn)
        layout.addWidget(counselor_records_btn)
        layout.addWidget(violations_records_btn)
        layout.addWidget(csh_records_btn)
        layout.addWidget(back_btn)
        
        self.setLayout(layout)


class StudentRecords(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        layout = QVBoxLayout()
        
        self.student_num = QLineEdit()
        self.student_num.setPlaceholderText("Enter Student Number")
        self.f_name = QLineEdit()
        self.f_name.setPlaceholderText("Enter First Name")
        self.l_name = QLineEdit()
        self.l_name.setPlaceholderText("Enter Last Name")
        self.program = QLineEdit()
        self.program.setPlaceholderText("Enter Program")
        
        submit_btn = QPushButton("Submit")
        back_btn = QPushButton("Back")
        
        submit_btn.clicked.connect(self.add_student)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        layout.addWidget(QLabel("Student Records"))
        layout.addWidget(self.student_num)
        layout.addWidget(self.f_name)
        layout.addWidget(self.l_name)
        layout.addWidget(self.program)
        layout.addWidget(submit_btn)
        layout.addWidget(back_btn)
        self.setLayout(layout)
                                 
        
    def add_student(self):
        studentno = self.student_num.text()
        student_fname = self.f_name.text()
        student_lname = self.l_name.text()
        student_prog = self.program.text()
        conn = connect_to_community_db()
        create_tables()
        if conn:
            cursor = conn.cursor()
            cursor.execute(""" INSERT INTO students 
                           (student_num, first_name, last_name, program)
                           VALUES (?, ?, ?, ?)
                           """, (studentno, student_fname, student_lname, student_prog))
            conn.commit()
            QMessageBox.information(self, "Success", "Student added successfully!")
            conn.close()
        
    

# Main Application
app = QApplication(sys.argv)
stacked_widget = QStackedWidget()

role_selection = RoleSelection(stacked_widget)
student_page = StudentPage(stacked_widget)
counselor_page = CounselorPage(stacked_widget)
admin_page = AdminPage(stacked_widget)
admin_ui = AdminMenu(stacked_widget)
student_record = StudentRecords(stacked_widget)
# counselor_record = CounselorRecords(stacked_widget)
# violations_record = ViolationRecords(stacked_widget)


stacked_widget.addWidget(role_selection)  # index 0
stacked_widget.addWidget(student_page)    # index 1
stacked_widget.addWidget(counselor_page)  # index 2
stacked_widget.addWidget(admin_page)      # index 3
stacked_widget.addWidget(admin_ui)        # index 4
stacked_widget.addWidget(student_record)  # index 5
# stacked_widget.addWidget(counselor_record) index 6
# stacked_widget.addWidget(violations_record) index 7
# stacked_widget.addWidget(csh_record) index 8

stacked_widget.setFixedSize(400, 300)
stacked_widget.setWindowTitle("Community Hours System")
stacked_widget.show()

sys.exit(app.exec_())