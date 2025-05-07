import sys
import pyodbc
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QStackedWidget


class CSH(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("T.I.P. C.S.H.")
        self.setGeometry(100, 100, 450, 400)

        # Server settings - update if necessary
        self.server = 'localhost\\SQLEXPRESS'  # Change if needed
        self.database = 'CSH'  # Database name

        self.create_database_if_not_exists()

        # Connect to the target database
        self.conn = pyodbc.connect(
            f'DRIVER={{SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes'
        )
        self.cursor = self.conn.cursor()
        self.create_tables()

        self.stack = QStackedWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def create_database_if_not_exists(self):
        # Connect to master to create database if missing
        temp_conn = pyodbc.connect(
            f'DRIVER={{SQL Server}};SERVER={self.server};DATABASE=master;Trusted_Connection=yes'
        )
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute(f"""
        IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'{self.database}')
        BEGIN
            CREATE DATABASE [{self.database}]
        END
        """)
        temp_conn.commit()
        temp_conn.close()

    def create_tables(self):
        self.cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='counselor' AND xtype='U'
        )
        CREATE TABLE counselor(
            counselor_id INT PRIMARY KEY IDENTITY(1,1),
            counselor_first_name VARCHAR(255),
            counselor_last_name VARCHAR(255),
            counselor_program VARCHAR(255)
        )
        """)

        self.cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='violations' AND xtype='U'
        )
        CREATE TABLE violations(
            violation_id INT PRIMARY KEY,
            violation_name VARCHAR(255),
            community_hours INT
        )
        """)

        self.cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='students' AND xtype='U'
        )
        CREATE TABLE students(
            student_num INT PRIMARY KEY,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            program VARCHAR(255)
        )
        """)

        self.cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='student_violations' AND xtype='U'
        )
        CREATE TABLE student_violations(
            sv_id INT PRIMARY KEY,
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
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='csh' AND xtype='U'
        )
        CREATE TABLE csh(
            sv_id INT NOT NULL,
            community_hours INT,
            time_in DATETIME,
            time_out DATETIME,
            counselor_id INT,
            remarks TEXT,
            FOREIGN KEY (sv_id) REFERENCES student_violations(sv_id),
            FOREIGN KEY (counselor_id) REFERENCES counselor(counselor_id)
        )
        """)
        self.conn.commit()


def main():
    app = QApplication(sys.argv)
    window = CSH()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
