import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QStackedWidget, QLineEdit, QComboBox, QMessageBox, QInputDialog, QHBoxLayout,
    QFormLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDateTime


class CSH(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("T.I.P. C.S.H.")
        self.setGeometry(100, 100, 450, 400)
        self.conn = sqlite3.connect("CSH.db")
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.stack = QStackedWidget()
        self.init_ui()
        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-image: url("C:/Users/TIPQC/Downloads/blackandyellow.jpg");
                background-repeat: no-repeat;
                background-position: left;
            }
        """)

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS counselor(
            counselor_id INTEGER PRIMARY KEY,
            counselor_first_name VARCHAR,
            counselor_last_name VARCHAR,
            counselor_program VARCHAR
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS violations(
            violation_id INT PRIMARY KEY NOT NULL,
            violation_name VARCHAR,
            community_hours INT
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS students(
            student_num INT PRIMARY KEY NOT NULL,
            first_name VARCHAR,
            last_name VARCHAR,
            program VARCHAR
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_violations(
            sv_id INT PRIMARY KEY NOT NULL,
            student_number INT,
            first_offense_id INT,
            second_offense_id INT,
            third_offense_id INT,
            FOREIGN KEY (student_number) REFERENCES students(student_num),
            FOREIGN KEY (first_offense_id) REFERENCES violations(violation_id),
            FOREIGN KEY (second_offense_id) REFERENCES violations(violation_id),
            FOREIGN KEY (third_offense_id) REFERENCES violations(violation_id)
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS csh(
            sv_id INT NOT NULL,
            community_hours INT,
            time_in DATETIME,
            time_out DATETIME,
            counselor_id INT,
            remarks LONGTEXT,
            FOREIGN KEY (sv_id) REFERENCES student_violations(sv_id),
            FOREIGN KEY (counselor_id) REFERENCES counselor(counselor_id)
        )
        """)
        self.conn.commit()
        
    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("COMMUNITY SERVICE HOURS")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        student_btn = QPushButton("STUDENT")
        admin_btn = QPushButton("ADMIN")
        counselor_btn = QPushButton("COUNSELOR")

        for btn in [student_btn, admin_btn, counselor_btn]:
            btn.setFixedSize(250, 60)
            btn.setStyleSheet("font-size: 18px; border: 2px solid black; background-color: none;")

        student_btn.clicked.connect(self.select_student)
        admin_btn.clicked.connect(self.check_admin)
        counselor_btn.clicked.connect(self.select_counselor)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(student_btn, alignment=Qt.AlignCenter)
        layout.addWidget(admin_btn, alignment=Qt.AlignCenter)
        layout.addWidget(counselor_btn, alignment=Qt.AlignCenter)
        layout.addStretch()
        
        

        self.setLayout(layout)
        
    def select_student(self):
        self.form_page.set_mode("student")
        self.stacked_widget.setCurrentIndex(1)

    def select_counselor(self):
        self.form_page.set_mode("counselor")
        self.stacked_widget.setCurrentIndex(1)

    def check_admin(self):
        id_text, ok1 = QInputDialog.getText(self, "Admin Login", "Enter Admin ID:")
        pw_text, ok2 = QInputDialog.getText(self, "Admin Login", "Enter Password:", QLineEdit.Password)
        if ok1 and ok2 and id_text == "admin" and pw_text == "1234":
            self.form_page.set_mode("admin")
            self.stacked_widget.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect ID or password.")
    
    
    def admin_user_ui(self):
        self.select_widget = QWidget()
        layout = QVBoxLayout()
        self.edit_students_btn = QPushButton("Edit Student Records")
        self.edit_students_btn.clicked.connect(self.edit_students_ui)
        self.edit_violations_btn = QPushButton("Edit Violation Records")
        self.edit_violations_btn.clicked.connect(self.edit_violations_ui)
        self.edit_counselor_btn = QPushButton("Edit Counselor Records")
        self.edit_counselor_btn.clicked.connect(self.edit_counselors_ui)
        layout.addWidget(self.edit_students_btn)
        layout.addWidget(self.edit_counselors_btn)
        layout.addWidget(self.edit_violations_btn)
        self.select_widget.setLayout(layout)
    
    def edit_students_ui(self):
        self.user_widget = QWidget()
        layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.student_num_input = QLineEdit()
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.program_input = QLineEdit()
        self.form_layout.addRow("Student Num: ", self.student_num_input)
        self.form_layout.addRow("First Name", self.first_name_input)
        self.form_layout.addRow("Last Name", self.last_name_input)
        self.form_layout.addRow("Program", self.program_input)
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.add_user)
        self.back_button = QPushButton("Back To Main Menu")
        self.back_button.clicked.connect(self.back)
        layout.addLayout(self.form_layout)
        layout.addWidget(self.register_button)
        layout.addWidget(self.back_button)
        self.user_widget.setLayout(layout)
        self.stack.addWidget(self.user_widget)
        self.stack.setCurrentWidget(self.user_widget)  
    
    def edit_violation_records(self):
        self.user_widget = QWidget()
        layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.violation_id_input = QLineEdit()
        self.violation_name_input = QLineEdit()
        self.community_hours_inpu = QLineEdit()
        self.program_input = QLineEdit()
        self.form_layout.addRow("Violation ID: ", self.violation_id_input)
        self.form_layout.addRow("Violation Name: ", self.violation_name_input)
        self.form_layout.addRow("Community Hours: ", self.community_hours_input)
        self.add_violation_button = QPushButton("Add Violation")
        self.add_violation_button.clicked.connect(self.add_violation)
        self.back_button = QPushButton("Back To Main Menu")
        self.back_button.clicked.connect(self.back)
        layout.addLayout(self.form_layout)
        layout.addWidget(self.add_violation_button)
        layout.addWidget(self.back_button)
        self.user_widget.setLayout(layout)
        self.stack.addWidget(self.user_widget)
        self.stack.setCurrentWidget(self.user_widget)
    
    def edit_counselor_records(self):
        self.user_widget = QWidget()
        layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.violation_id_input = QLineEdit()
        self.violation_name_input = QLineEdit()
        self.community_hours_inpu = QLineEdit()
        self.program_input = QLineEdit()
        self.form_layout.addRow("Counselor ID: ", self.counselor_id_input)
        self.form_layout.addRow("First Name: ", self.counselor_fname_input)
        self.form_layout.addRow("Last Name: ", self.counselor_lname_input)
        self.form_layout.addRow("Program: ", self.counselor_program_input)
        self.add_counselor_button_button = QPushButton("Register")
        self.add_counselor_button.clicked.connect(self.add_counselor)
        self.back_button = QPushButton("Back To Main Menu")
        self.back_button.clicked.connect(self.back)
        layout.addLayout(self.form_layout)
        layout.addWidget(self.add_counselor_button)
        layout.addWidget(self.back_button)
        self.user_widget.setLayout(layout)
        self.stack.addWidget(self.user_widget)
        self.stack.setCurrentWidget(self.user_widget) 
    
    def back(self):
        self.admin_user_ui()
        self.stack.setCurrentWidget(self.select_widget)
        QMessageBox.information(self, "", "Returning to Main Menu...")
        

def main():
    app = QApplication(sys.argv)
    window = CSH()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
