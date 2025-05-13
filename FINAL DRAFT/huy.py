import sys
import pyodbc
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QMessageBox, QStackedWidget, QTableWidget, QTableWidgetItem

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
                name VARCHAR(30),
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
                third_offense_id INT FOREIGN KEY REFERENCES violations(violation_id),
                remaining_hours INT
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

from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox

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
        student_number = self.id_input.text()
        conn = connect_to_community_db()
        if not conn:
            QMessageBox.critical(self, "Error", "Database connection failed.")
            return

        cursor = conn.cursor()

        # Get the sv_id from student_violations
        cursor.execute("SELECT sv_id FROM student_violations WHERE student_number = ?", (student_number,))
        sv = cursor.fetchone()
        if not sv:
            QMessageBox.warning(self, "Error", "Student not found in student_violations.")
            conn.close()
            return

        sv_id = sv[0]

        # Check if student already timed in
        cursor.execute("SELECT sv_id, time_out FROM csh WHERE sv_id = ? AND time_in IS NULL", (sv_id,))
        active_session = cursor.fetchone()

        if active_session:
            # Perform time-out
            csh_id, time_in = active_session
            time_out = datetime.now()
            duration = (time_out - time_in).total_seconds() / 3600.0

            # Update time_out in csh
            cursor.execute("UPDATE csh SET time_out = ?, remarks = 'Completed' WHERE id = ?", (time_out, csh_id))

            # Deduct hours
            cursor.execute("""
                UPDATE student_violations 
                SET remaining_hours = remaining_hours - ? 
                WHERE sv_id = ?
            """, (duration, sv_id))

            conn.commit()
            QMessageBox.information(self, "Timed Out", f"Time-out successful. {duration:.2f} hrs subtracted.")

        else:
            # Perform time-in
            time_in = datetime.now()
            cursor.execute("INSERT INTO csh (sv_id, time_in, remarks) VALUES (?, ?, ?)", (sv_id, time_in, 'Not Completed'))
            conn.commit()
            QMessageBox.information(self, "Timed In", "Time-in recorded successfully.")

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
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT department_1, department_2 FROM counselors WHERE counselor_id = ? AND password = ?",
                    (counselor_id, password)
                )
                result = cursor.fetchone()
                if result:
                    dept1, dept2 = result
                    QMessageBox.information(self, "Success", "Counselor logged in successfully!")
                    counselor_menu = CounselorMenu(self.stacked_widget, [dept1, dept2])
                    self.stacked_widget.addWidget(counselor_menu)
                    self.stacked_widget.setCurrentWidget(counselor_menu)
                else:
                    QMessageBox.warning(self, "Failed", "Invalid credentials.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Login error: {e}")
            finally:
                conn.close()
                
class CounselorMenu(QWidget):
    def __init__(self, stacked_widget, departments):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.departments = departments if isinstance(departments, list) else [departments]

        layout = QVBoxLayout()
        self.students_btn = QPushButton("View Students")
        self.violations_btn = QPushButton("View Violations")
        self.csh_btn = QPushButton("View Community Hours")
        back_btn = QPushButton("Back")

        self.students_btn.clicked.connect(self.show_students_table)
        self.violations_btn.clicked.connect(self.show_violations_table)
        self.csh_btn.clicked.connect(self.show_csh_table)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        layout.addWidget(QLabel(f"Counselor View - Programs: {', '.join(self.departments)}"))
        layout.addWidget(self.students_btn)
        layout.addWidget(self.violations_btn)
        layout.addWidget(self.csh_btn)
        layout.addWidget(back_btn)
        self.setLayout(layout)

    def fetch_data(self, query, params):
        conn = connect_to_community_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        data = cursor.fetchall()
        headers = [column[0] for column in cursor.description]
        conn.close()
        return headers, data

    def fetch_student_nums(self):
        query = f"SELECT student_num FROM students WHERE program IN ({','.join(['?'] * len(self.departments))})"
        conn = connect_to_community_db()
        cursor = conn.cursor()
        cursor.execute(query, self.departments)
        student_nums = [row[0] for row in cursor.fetchall()]
        conn.close()
        return student_nums

    def show_students_table(self):
        query = f"SELECT * FROM students WHERE program IN ({','.join(['?'] * len(self.departments))})"
        headers, data = self.fetch_data(query, self.departments)
        self.display_table_page("Students", headers, data)

    def show_violations_table(self):
        student_nums = self.fetch_student_nums()
        if not student_nums:
            QMessageBox.information(self, "Violations", "No student violations found.")
            return

        query = f"""
            SELECT sv.sv_id, sv.student_number, s.first_name, s.last_name,
                   v1.violation_name AS first_offense,
                   v2.violation_name AS second_offense,
                   v3.violation_name AS third_offense
            FROM student_violations sv
            JOIN students s ON sv.student_number = s.student_num
            LEFT JOIN violations v1 ON sv.first_offense_id = v1.violation_id
            LEFT JOIN violations v2 ON sv.second_offense_id = v2.violation_id
            LEFT JOIN violations v3 ON sv.third_offense_id = v3.violation_id
            WHERE sv.student_number IN ({','.join(['?'] * len(student_nums))})
        """
        headers, data = self.fetch_data(query, student_nums)
        self.display_table_page("Student Violations", headers, data)

    def show_csh_table(self):
        student_nums = self.fetch_student_nums()
        if not student_nums:
            QMessageBox.information(self, "Community Hours", "No CSH records found.")
            return

        query = f"""
            SELECT c.sv_id, sv.student_number, s.first_name, s.last_name,
                   c.time_in, c.time_out, c.counselor_id, c.remarks
            FROM csh c
            JOIN student_violations sv ON c.sv_id = sv.sv_id
            JOIN students s ON sv.student_number = s.student_num
            WHERE sv.student_number IN ({','.join(['?'] * len(student_nums))})
        """
        headers, data = self.fetch_data(query, student_nums)
        self.display_table_page("Community Service Hours", headers, data)

    def display_table_page(self, title, headers, data):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel(title)
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)

        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(headers)

        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        table.resizeColumnsToContents()
        layout.addWidget(table)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self))
        layout.addWidget(back_btn)

        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
        self.stacked_widget.setCurrentWidget(page)
        
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
        student_violations_btn = QPushButton("Edit Student Violations Record")
        csh_records_btn = QPushButton("Edit Community Hours Record")
        back_btn = QPushButton("Back")
        

        student_records_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(5))
        counselor_records_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(6))
        violations_records_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(8))
        student_violations_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(9))
        csh_records_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(10))
        back_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
        layout.addWidget(student_records_btn)
        layout.addWidget(counselor_records_btn)
        layout.addWidget(violations_records_btn)
        layout.addWidget(student_violations_btn)
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
            self.stacked_widget.setCurrentIndex(4)
            conn.close()
            
class CounselorRecords(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        layout = QVBoxLayout()
        
        self.counselor_id = QLineEdit()
        self.counselor_id.setPlaceholderText("Enter Counselor ID")
        self.name = QLineEdit()
        self.name.setPlaceholderText("Enter Full Name")
        self.dept_1 = QLineEdit()
        self.dept_1.setPlaceholderText("Enter Department 1")
        self.dept_2 = QLineEdit()
        self.dept_2.setPlaceholderText("Enter Department 2")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Enter Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        
        
        submit_btn = QPushButton("Submit")
        back_btn = QPushButton("Back")
        
        submit_btn.clicked.connect(self.add_counselor)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        layout.addWidget(QLabel("Counselor Records"))
        layout.addWidget(self.counselor_id)
        layout.addWidget(self.name)
        layout.addWidget(self.dept_1)
        layout.addWidget(self.dept_2)
        layout.addWidget(self.pass_input)
        layout.addWidget(submit_btn)
        layout.addWidget(back_btn)
        self.setLayout(layout)
                                 
        
    def add_counselor(self):
        couns_id = self.counselor_id.text()
        couns_name = self.name.text()
        couns_dept1 = self.dept_1.text()
        couns_dept2 = self.dept_2.text()
        password = self.pass_input.text()
        conn = connect_to_community_db()
        create_tables()
        if conn:
            cursor = conn.cursor()
            cursor.execute(""" INSERT INTO counselors 
                           (counselor_id, name, department_1, department_2, password)
                           VALUES (?, ?, ?, ?, ?)
                           """, (couns_id, couns_name, couns_dept1, couns_dept2, password))
            conn.commit()
            QMessageBox.information(self, "Success", "Counselor added successfully!")
            self.stacked_widget.setCurrentIndex(4)
            conn.close()
        

class ViolationRecords(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        layout = QVBoxLayout()
        
        self.violation_name = QLineEdit()
        self.violation_name.setPlaceholderText("Enter Violation Name")
        self.community_hours= QLineEdit()
        self.community_hours.setPlaceholderText("Enter Community Hours")
        
        
        submit_btn = QPushButton("Submit")
        back_btn = QPushButton("Back")
        
        submit_btn.clicked.connect(self.add_violation)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))
        
        layout.addWidget(QLabel("Violation Records"))
        layout.addWidget(self.violation_name)
        layout.addWidget(self.community_hours)
        layout.addWidget(submit_btn)
        layout.addWidget(back_btn)
        self.setLayout(layout)
                                 
        
    def add_violation(self):
        viol_name = self.violation_name.text()
        comm_hours = self.community_hours.text()
        conn = connect_to_community_db()
        create_tables()
        if conn:
            cursor = conn.cursor()
            cursor.execute(""" INSERT INTO violations 
                           (violation_name, community_hours)
                           VALUES (?, ?)
                           """, (viol_name, comm_hours))
            conn.commit()
            QMessageBox.information(self, "Success", "Violation added successfully!")
            self.stacked_widget.setCurrentIndex(4)
            conn.close()

class StudentViolations(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        layout = QVBoxLayout()
        
        self.student_number = QLineEdit()
        self.student_number.setPlaceholderText("Enter Student Number")
        self.first_offense_id= QLineEdit()
        self.first_offense_id.setPlaceholderText("Enter First Offense")
        self.second_offense_id = QLineEdit()
        self.second_offense_id.setPlaceholderText("Enter Second Offense")
        self.third_offense_id = QLineEdit()
        self.third_offense_id.setPlaceholderText("Enter Third Offense")
        
        
        submit_btn = QPushButton("Submit")
        back_btn = QPushButton("Back")
        
        submit_btn.clicked.connect(self.add_studentviolation)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))
        
        layout.addWidget(QLabel("Student Violation Records"))
        layout.addWidget(self.student_number)
        layout.addWidget(self.first_offense_id)
        layout.addWidget(self.second_offense_id)
        layout.addWidget(self.third_offense_id)
        layout.addWidget(submit_btn)
        layout.addWidget(back_btn)
        self.setLayout(layout)
                                 
        
    def add_studentviolation(self):
        stdt_no = self.student_number.text()
        first_offense = self.first_offense_id.text()
        second_offense = self.second_offense_id.text()
        third_offense = self.third_offense_id.text()
        conn = connect_to_community_db()
        create_tables()
        if conn:
            cursor = conn.cursor()
            def get_hours(offense_id):
                if offense_id:
                    cursor.execute("SELECT community_hours FROM violations WHERE violation_id = ?", (offense_id,))
                    result = cursor.fetchone()
                    return result[0] if result else 0
                return 0

        first_hours = get_hours(first_offense)
        second_hours = get_hours(second_offense)
        third_hours = get_hours(third_offense)

        total_hours = first_hours + second_hours + third_hours

        cursor.execute(""" INSERT INTO student_violations 
                           (student_number, first_offense_id, second_offense_id, third_offense_id, remaining_hours)
                           VALUES (?, ?, ?, ?, ?)
                           """, (stdt_no, first_offense or None, second_offense or None, third_offense or None, total_hours))
        conn.commit()
        QMessageBox.information(self, "Success", "Student recorded successfully!")
        self.stacked_widget.setCurrentIndex(4)
        conn.close()

class CSH(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        layout = QVBoxLayout()
        
        self.sv_id = QLineEdit()
        self.sv_id.setPlaceholderText("Enter S.V. ID")
        self.counselor_id = QLineEdit()
        self.counselor_id.setPlaceholderText("Enter Counselor ID")
        
        
        submit_btn = QPushButton("Submit")
        back_btn = QPushButton("Back")
        
        submit_btn.clicked.connect(self.add_csh)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))
        
        layout.addWidget(QLabel("CSH"))
        layout.addWidget(self.sv_id)
        layout.addWidget(self.counselor_id)
        layout.addWidget(submit_btn)
        layout.addWidget(back_btn)
        self.setLayout(layout)
                                 
        
    def add_csh(self):
        sv_ID = self.sv_id.text()
        couns_ID = self.counselor_id.text()
        conn = connect_to_community_db()
        create_tables()
        if conn:
            cursor = conn.cursor()
            cursor.execute(""" INSERT INTO csh
                           (sv_id, counselor_id, remarks)
                           VALUES (?, ?, ?)
                           """, (sv_ID, couns_ID, 'Not Completed'))
        conn.commit()
        QMessageBox.information(self, "Success", "Student recorded successfully!")
        self.stacked_widget.setCurrentIndex(4)
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
counselor_record = CounselorRecords(stacked_widget)
student_violation = StudentViolations(stacked_widget)
violations_record = ViolationRecords(stacked_widget)
csh_record = CSH(stacked_widget)
counselor_menu = QWidget()


stacked_widget.addWidget(role_selection)  # index 0
stacked_widget.addWidget(student_page)    # index 1
stacked_widget.addWidget(counselor_page)  # index 2
stacked_widget.addWidget(admin_page)      # index 3
stacked_widget.addWidget(admin_ui)        # index 4
stacked_widget.addWidget(student_record)  # index 5
stacked_widget.addWidget(counselor_record) # index 6
stacked_widget.addWidget(counselor_menu)   # index 7
stacked_widget.addWidget(violations_record) # index 8
stacked_widget.addWidget(student_violation) # index 9
stacked_widget.addWidget(csh_record) # index 10

stacked_widget.setFixedSize(400, 300)
stacked_widget.setWindowTitle("Community Hours System")
stacked_widget.show()

sys.exit(app.exec_())
