import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QFormLayout, QDateEdit, QMessageBox, QStackedWidget, QHBoxLayout, QListWidget
from PyQt5.QtGui import QIcon


class CSH(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("T.I.P. C.S.H.")
        self.setGeometry(100, 100, 450, 400)
        self.conn = sqlite3.connect("CSH.db")
        self.cursor = self.conn.cursor()
        self.create_tables()
        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS counselor(
            counselor_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            program VARCHAR)
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
            FOREIGN KEY (third_offense_id) REFERENCES violations(violation_id),
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
        
# Create GUIs based on the tables given by using functions.
# Admin access should be able to do the CRUD in database.
# Students must be registered in the database first, in order to be able to 
# time in and time out.
# Counselor could also login to view the students that he/she observes.
def main():
    app = QApplication(sys.argv)
    window = CSH()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()



