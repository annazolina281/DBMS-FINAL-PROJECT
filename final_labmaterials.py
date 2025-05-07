import sys
import csv
from PyQt5 import QtWidgets, QtGui, QtCore
from datetime import datetime
import pytz

tz = pytz.timezone('Asia/Manila')
current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

class Material:
    """Class to represent a laboratory material with a name and quantity."""
    def __init__(self, name, quantity):
        self.name = name
        self.quantity = quantity

class AccountManager:
    """Class to manage user accounts."""
    def __init__(self, filename='accounts.txt'):
        self.filename = filename

    def register(self, name, student_number):
        """Register a new user if the name or student number does not already exist."""
        with open(self.filename, 'a+') as file:
            file.seek(0)
            for line in file:
                existing_name, existing_number = line.strip().split(',')
                if existing_name == name or existing_number == student_number:
                    return False  # User already exists
            file.write(f"{name},{student_number}\n")  # Save new user
        return True  # Registration successful

    def login(self, name, student_number):
        """Check if the provided credentials match an existing account."""
        with open(self.filename, 'r') as file:
            for line in file:
                existing_name, existing_number = line.strip().split(',')
                if existing_name == name and existing_number == student_number:
                    return True  # Login successful
        return False  # Credentials incorrect

class DatabaseManager:
    """Class to manage materials in the database."""
    def __init__(self, filename='database.txt'):
        self.filename = filename
        self.materials = self.load_materials()

    def load_materials(self):
        """Load materials from the database file."""
        materials = {}
        try:
            with open(self.filename, 'r') as file:
                for line in file:
                    name, quantity = line.strip().split(',')
                    materials[name] = int(quantity)
        except FileNotFoundError:
            pass  # If the file doesn't exist, return an empty dictionary
        return materials

    def save_materials(self):
        """Save materials to the database file."""
        with open(self.filename, 'w') as file:
            for name, quantity in self.materials.items():
                file.write(f"{name},{quantity}\n")

    def add_material(self, name, quantity):
        """Add a new material or update the quantity."""
        self.materials[name] = quantity
        self.save_materials()

    def remove_material(self, name):
        """Remove a material from the database."""
        if name in self.materials:
            del self.materials[name]
            self.save_materials()

class BorrowingApp(QtWidgets.QWidget):
    """Main application for borrowing laboratory materials."""
    def __init__(self, student_name, student_number):
        super().__init__()
        self.student_name = student_name
        self.student_number = student_number
        self.materials = []  # List to hold borrowed materials
        self.db_manager = DatabaseManager()  # Initialize database manager
        self.init_ui()  # Initialize the user interface

    def init_ui(self):
        """Set up the user interface for borrowing materials."""
        self.setWindowTitle('Laboratory Materials Borrowing')
        self.setFixedSize(1910, 980)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Label for title
        title_label = QtWidgets.QLabel("Laboratory Materials Borrowing", self)
        title_label.setAlignment(QtCore.Qt.AlignCenter)  # Center the title

        # Set the font
        font = QtGui.QFont("Helvetica", 24, QtGui.QFont.Bold)
        title_label.setFont(font)

        # Set the text color to Maroon
        title_label.setStyleSheet("color: Maroon;")

        # Add the title label to the layout
        self.layout.addWidget(title_label)

        # Label for borrowing date and time
        self.date_time_label = QtWidgets.QLabel(f"Borrowing Date and Time: {current_time}")
        self.date_time_label.setFixedHeight(50)  # Set a fixed height
        self.date_time_label.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.layout.addWidget(self.date_time_label)

        # Label for materials input
        self.material_label = QtWidgets.QLabel("Select laboratory materials and their quantities:")
        self.material_label.setFixedHeight(50)  # Set a fixed height
        self.material_label.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.layout.addWidget(self.material_label)

        # Dropdown for materials
        self.material_combo = QtWidgets.QComboBox(self)
        self.material_combo.setEditable(True)  # Allow searching
        for material_name, quantity in self.db_manager.materials.items():
            self.material_combo.addItem(material_name)  # Only show the name
            self.material_combo.setItemData(self.material_combo.count() - 1, quantity)  # Set availability as data
        self.material_combo.setFixedHeight(50)  # Set a fixed height
        self.material_combo.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.layout.addWidget(self.material_combo)

        # QLabel to display available quantity
        self.available_label = QtWidgets.QLabel("Available: 0", self)
        self.available_label.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.layout.addWidget(self.available_label)

        # Connect the currentIndexChanged signal to update the available quantity
        self.material_combo.currentIndexChanged.connect(self.update_available_quantity)

        # Input field for material quantity
        self.quantity_input = QtWidgets.QSpinBox(self)
        self.quantity_input.setRange(1, 100)  # Range for quantity
        self.quantity_input.setFixedHeight(50)  # Set a fixed height
        self.quantity_input.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.layout.addWidget(self.quantity_input)

        # Button to add material
        self.add_button = QtWidgets.QPushButton("Add Material")
        self.add_button.setFixedHeight(50)  # Set a fixed height
        self.add_button.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.add_button.clicked.connect(self.add_material)  # Connect button to add_material method
        self.layout.addWidget(self.add_button)

        # Button to remove material
        self.remove_button = QtWidgets.QPushButton("Remove Selected Material")
        self.remove_button.setFixedHeight(50)  # Set a fixed height
        self.remove_button.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.remove_button.clicked.connect(self.remove_material)  # Connect button to remove_material method
        self.layout.addWidget(self.remove_button)

        # Button to finish borrowing
        self.finish_button = QtWidgets.QPushButton("Finish Borrowing")
        self.finish_button.setFixedHeight(50)  # Set a fixed height
        self.finish_button.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.finish_button.clicked.connect(self.finish_borrowing)  # Connect button to finish_borrowing method
        self.layout.addWidget(self.finish_button)

        # List widget to display added materials
        self.materials_list = QtWidgets.QListWidget(self)
        self.layout.addWidget(self.materials_list)

        # Adding the back button
        self.back_button = QtWidgets.QPushButton("Back")
        self.back_button.setFixedHeight(50)  # Set a fixed height
        self.back_button.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.back_button.clicked.connect(self.go_back)
        self.layout.addWidget(self.back_button)

    # Method to update the available quantity label
    def update_available_quantity(self):
        current_index = self.material_combo.currentIndex()  # Get the current index
        available_quantity = self.material_combo.itemData(current_index)  # Get the available quantity
        self.available_label.setText(f"Available: {available_quantity}")  # Update the label text

    def add_material(self):
        """Add a material to the borrowing list."""
        if len(self.materials) >= 12:
            QtWidgets.QMessageBox.warning(self, "Limit Reached",
                                          "You can only borrow up to 12 different types of materials.")
            return

        material_name = self.material_combo.currentText().strip()  # Get material name from dropdown
        quantity = self.quantity_input.value()  # Get material quantity input

        # If the material name is valid, add it to the list
        if material_name and material_name in self.db_manager.materials:
            available_quantity = self.db_manager.materials[material_name]
            if quantity > available_quantity:
                QtWidgets.QMessageBox.warning(self, "Quantity Error",
                                              f"Only {available_quantity} available for {material_name}.")
                return

            # Append material to the list
            self.materials.append(Material(material_name, quantity))
            self.materials_list.addItem(f"{material_name}: {quantity}")  # Update the displayed list

            # Update the database or the source of materials
            self.db_manager.materials[material_name] -= quantity  # Decrease available quantity

            # Refresh the ComboBox
            self.material_combo.clear()  # Clear the dropdown for new input
            for name, qty in self.db_manager.materials.items():
                self.material_combo.addItem(name)  # Add material name
                self.material_combo.setItemData(self.material_combo.count() - 1, qty)  # Set available quantity as data

            # Reset the available quantity label
            self.update_available_quantity()  # Update the label to reflect the current selected material's availability

            self.quantity_input.setValue(1)  # Reset quantity to default

    def remove_material(self):
        """Remove a selected material from the borrowing list."""
        selected_item = self.materials_list.currentItem()  # Get the selected item
        if selected_item:
            material_name = selected_item.text().split(':')[0]  # Extract material name
            # Find the material in the materials list and remove it
            for material in self.materials:
                if material.name == material_name:
                    self.materials.remove(material)  # Remove material from the list
                    break
            self.materials_list.takeItem(self.materials_list.row(selected_item))  # Remove from the displayed list
        else:
            QtWidgets.QMessageBox.warning(self, "Selection Error", "Please select a material to remove.")

    def finish_borrowing(self):
        """Finalize the borrowing process and log the information."""
        if not self.materials:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please add at least one material.")
            return

        # Get the current date and time in Philippine Standard Time
        tz = pytz.timezone('Asia/Manila')
        current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")  # Format date and time

        # Prepare borrowing information for display
        borrowing_info = f"Borrowing Information:\nDate and Time: {current_time}\nBorrower: {self.student_name} ({self.student_number})\nMaterials Borrowed:\n"
        for material in self.materials:
            borrowing_info += f"- {material.name}: {material.quantity}\n"

        # Show the borrowing information in a message box
        QtWidgets.QMessageBox.information(self, "Borrowing Information", borrowing_info)
        self.log_borrowing(current_time)  # Log the borrowing details
        self.update_database()  # Update the database with borrowed quantities
        self.clear_inputs()  # Clear inputs for the next borrowing session.

    def log_borrowing(self, current_time):
        """Log the borrowing information to a CSV file, including the borrower's name."""
        with open('log.csv', 'a', newline='') as log_file:
            log_writer = csv.writer(log_file)

            # Write the header only if the file is empty
            if log_file.tell() == 0:
                log_writer.writerow(['Borrower', 'Student Number', 'Date', 'Materials'])  # Write header

            # Write the borrowing details to the log file
            materials_borrowed = "; ".join([f"{material.name}:{material.quantity}" for material in self.materials])
            log_writer.writerow([self.student_name, self.student_number, current_time, materials_borrowed])

    def update_database(self):
        """Update the database to reflect the quantities of borrowed materials."""
        for material in self.materials:
            if material.name in self.db_manager.materials:
                self.db_manager.materials[material.name] -= material.quantity  # Subtract borrowed quantity
                if self.db_manager.materials[material.name] < 0:
                    self.db_manager.materials[material.name] = 0  # Prevent negative stock
        self.db_manager.save_materials()  # Save updated materials to the database file

    def clear_inputs(self):
        """Clear the input fields and materials list for a new borrowing session."""
        self.materials.clear()  # Clear the materials list
        self.materials_list.clear()  # Clear the displayed materials
        self.material_combo.clear()  # Clear the material dropdown
        self.material_combo.addItems(self.db_manager.materials.keys())  # Refresh dropdown items
        self.quantity_input.setValue(1)  # Reset quantity to default

    def go_back(self):
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

class AdminApp(QtWidgets.QWidget):
    """ Admin application for managing materials."""
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()  # Initialize database manager
        self.init_ui()  # Initialize the user interface

    def init_ui(self):
        """Set up the user interface for the admin application."""
        self.setWindowTitle('Admin Materials Management')
        self.setFixedSize(1910, 980)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Label for materials management
        title_label = QtWidgets.QLabel("Materials Manager", self)
        title_label.setAlignment(QtCore.Qt.AlignCenter)  # Center the title

        # Set the font
        font = QtGui.QFont("Helvetica", 24, QtGui.QFont.Bold)
        title_label.setFont(font)

        # Set the text color to blue
        title_label.setStyleSheet("color: blue;")

        self.layout.addWidget(title_label)  # Add the title label to the layout

        # Input field for material name
        self.material_name_input = QtWidgets.QLineEdit(self)
        self.material_name_input.setPlaceholderText("Material name")
        self.material_name_input.setFixedHeight(50)  # Set a fixed height
        self.material_name_input.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.layout.addWidget(self.material_name_input)

        # Input field for material quantity
        self.quantity_input = QtWidgets.QSpinBox(self)
        self.quantity_input.setRange(1, 100)  # Range for quantity
        self.quantity_input.setFixedHeight(50)  # Set a fixed height
        self.quantity_input.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.layout.addWidget(self.quantity_input)

        # Button to add/update material
        self.add_button = QtWidgets.QPushButton("Add/Update Material")
        self.add_button.setFixedHeight(50)  # Set a fixed height
        self.add_button.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.add_button.clicked.connect(self.add_update_material)  # Connect button to add_update_material method
        self.layout.addWidget(self.add_button)

        # Button to remove material
        self.remove_button = QtWidgets.QPushButton("Remove Material")
        self.remove_button.setFixedHeight(50)  # Set a fixed height
        self.remove_button.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.remove_button.clicked.connect(self.remove_material)  # Connect button to remove_material method
        self.layout.addWidget(self.remove_button)

        # List widget to display materials
        self.materials_list = QtWidgets.QListWidget(self)
        self.update_materials_list()  # Populate the list with current materials
        self.layout.addWidget(self.materials_list)

        # Adding the back button
        self.back_button = QtWidgets.QPushButton("Back")
        self.back_button.setFixedHeight(50)  # Set a fixed height
        self.back_button.setFont(QtGui.QFont("Helvetica", 16))  # Set font size
        self.back_button.clicked.connect(self.go_back)
        self.layout.addWidget(self.back_button)

    def add_update_material(self):
        """Add a new material or update an existing one."""
        material_name = self.material_name_input.text().strip()  # Get material name input
        quantity = self.quantity_input.value()  # Get material quantity input

        if material_name:
            self.db_manager.add_material(material_name, quantity)  # Add or update material in the database
            self.update_materials_list()  # Refresh the materials list
            self.material_name_input.clear()  # Clear the input field
            self.quantity_input.setValue(1)  # Reset quantity to default

    def remove_material(self):
        """Remove a selected material from the database."""
        selected_item = self.materials_list.currentItem()  # Get the selected item
        if selected_item:
            material_name = selected_item.text().split(':')[0]  # Extract material name
            self.db_manager.remove_material(material_name)  # Remove material from the database
            self.update_materials_list()  # Refresh the materials list

    def update_materials_list(self):
        """Update the displayed list of materials."""
        self.materials_list.clear()  # Clear the current list
        for name, quantity in self.db_manager.materials.items():
            self.materials_list.addItem(f"{name}: {quantity}")  # Add materials to the list

    def go_back(self):
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

class LoginWindow(QtWidgets.QWidget):
    """Login window for entering student information."""
    def __init__(self):
        super().__init__()
        self.account_manager = AccountManager()  # Initialize account manager
        self.init_ui()  # Initialize the user interface

    def init_ui(self):
        """Set up the user interface for the login window."""
        self.setWindowTitle('Login / Registration')
        self.setFixedSize(1910, 980)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Create a frame for the title label
        title_frame = QtWidgets.QFrame(self)
        title_frame.setFrameShape(QtWidgets.QFrame.Box)  # Set the frame shape to Box
        title_frame.setStyleSheet("border: 2px solid indigo;")  # Set the border color and style

        # Label for title
        title_label = QtWidgets.QLabel("LABORATORY MATERIALS\nLogin / Registration", self)
        title_label.setAlignment(QtCore.Qt.AlignCenter)  # Center the title

        # Set the font
        font = QtGui.QFont("Helvetica", 24, QtGui.QFont.Bold)
        title_label.setFont(font)

        # Set the text color to indigo
        title_label.setStyleSheet("color: indigo;")

        # Create a layout for the title frame and add the title label to it
        title_layout = QtWidgets.QVBoxLayout(title_frame)
        title_layout.addWidget(title_label)  # Add the title label to the frame's layout

        # Set the layout for the title frame
        title_frame.setLayout(title_layout)

        # Add the title frame to the main layout
        self.layout.addWidget(title_frame)

        # Input field for student name
        self.name_input = QtWidgets.QLineEdit(self)
        self.name_input.setPlaceholderText("Enter your name")
        self.name_input.setFixedHeight(50)  # Set a fixed height
        font = QtGui.QFont("Helvetica", 16)  # Increase font size
        self.name_input.setFont(font)
        self.layout.addWidget(self.name_input)

        # Input field for student number
        self.number_input = QtWidgets.QLineEdit(self)
        self.number_input.setPlaceholderText("Enter your student number")
        self.number_input.setFixedHeight(50)  # Set a fixed height
        self.number_input.setFont(font)  # Use the same font size
        self.layout.addWidget(self.number_input)

        # Button to log in
        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.setFixedHeight(50)  # Set a fixed height
        self.login_button.setFont(QtGui.QFont("Helvetica", 16))  # Increase font size
        self.login_button.clicked.connect(self.login)  # Connect button to login method
        self.layout.addWidget(self.login_button)

        # Button to register
        self.register_button = QtWidgets.QPushButton("Register")
        self.register_button.setFixedHeight(50)  # Set a fixed height
        self.register_button.setFont(QtGui.QFont("Helvetica", 16))  # Increase font size
        self.register_button.clicked.connect(self.register)  # Connect button to register method
        self.layout.addWidget(self.register_button)

    def login(self):
        """Handle the login process."""
        student_name = self.name_input.text().strip()  # Get student name input
        student_number = self.number_input.text().strip()  # Get student number input

        if student_name == "Admin" and student_number == "admin":
            self.close()  # Close the login window
            self.open_admin_app()  # Open the admin application
        elif student_name == "" and student_number == "":
            QtWidgets.QMessageBox.warning(self, "Login Error", "No Input. Please try again.")
        elif student_name == "" or student_number == "":
            QtWidgets.QMessageBox.warning(self, "Login Error", "Missing Input. Please try again.")
        elif self.account_manager.login(student_name, student_number):
            self.close()  # Close the login window
            self.open_borrowing_app(student_name, student_number)  # Open the borrowing application
        else:
            QtWidgets.QMessageBox.warning(self, "Login Error", "Incorrect credentials. Please try again.")

    def register(self):
        """Handle the registration process."""
        student_name = self.name_input.text().strip()  # Get student name input
        student_number = self.number_input.text().strip()  # Get student number input

        if not student_name or not student_number:
            QtWidgets.QMessageBox.warning(self, "Registration Error", "Name and student number cannot be blank.")
        elif not student_number.isdigit():
            QtWidgets.QMessageBox.warning(self, "Registration Error", "Student number must consist of integers only.")
        elif self.account_manager.register(student_name, student_number):
            QtWidgets.QMessageBox.information(self, "Registration Successful", "You have been registered!")
        elif student_name == "" and student_number == "":
            QtWidgets.QMessageBox.warning(self, "Registration Error", "No Input. Please try again.")
        elif student_name == "" or student_number == "":
            QtWidgets.QMessageBox.warning(self, "Registration Error", "Missing Input. Please try again.")
        else:
            QtWidgets.QMessageBox.warning(self, "Registration Error", "Name or student number already exists.")

    def open_borrowing_app(self, student_name, student_number):
        """Open the borrowing application with the provided student information."""
        self.borrowing_app = BorrowingApp(student_name, student_number)
        self.borrowing_app.show()

    def open_admin_app(self):
        """Open the admin application."""
        self.admin_app = AdminApp()
        self.admin_app.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    login_window = LoginWindow()  # Create the login window
    login_window.show()  # Show the login window
    sys.exit(app.exec_())  # Start the application event loop