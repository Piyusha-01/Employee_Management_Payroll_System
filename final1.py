import tkinter as tk
from tkinter import simpledialog, messagebox
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import tkinter.font as font
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import scrolledtext



# SQLite database setup
conn = sqlite3.connect('employee_payroll.db')
cursor = conn.cursor()

def create_employee_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            emp_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            department TEXT NOT NULL,
            basic_salary REAL NOT NULL,
            doj TEXT NOT NULL,
            overtime_hours INTEGER NOT NULL,
            bank_name TEXT NOT NULL,
            bank_account_number TEXT NOT NULL,
            ifsc_code TEXT NOT NULL,
            mobile_number TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')
    conn.commit()

class Employee:
    def __init__(self, emp_id, name, position, department, basic_salary, doj, overtime_hours=0,
                 bank_name="", bank_account_number="", ifsc_code="", mobile_number="", email=""):
        self.emp_id = emp_id
        self.name = name
        self.position = position
        self.department = department
        self.basic_salary = float(basic_salary)
        self.doj = doj
        self.overtime_hours = int(overtime_hours)
        self.allowances = {'Travel Allowance': 1000, 'Medical Allowance': 500}
        self.deductions = {'Tax': 500, 'Insurance': 200}
        self.bank_name = bank_name
        self.bank_account_number = bank_account_number
        self.ifsc_code = ifsc_code
        self.mobile_number = mobile_number
        self.email = email

    def validate_employee_data(self):
        if not self.name:
            raise ValueError("Name cannot be empty.")
        if not self.position:
            raise ValueError("Position cannot be empty.")
        if not self.department:
            raise ValueError("Department cannot be empty.")
        if self.basic_salary < 0:
            raise ValueError("Basic salary cannot be negative.")
        for allowance_name, allowance_amount in self.allowances.items():
            if allowance_amount < 0:
                raise ValueError(f"Allowance '{allowance_name}' cannot be negative.")
        for deduction_name, deduction_amount in self.deductions.items():
            if deduction_amount < 0:
                raise ValueError(f"Deduction '{deduction_name}' cannot be negative.")

def insert_employee(employee):
    try:
        employee.validate_employee_data()
        cursor.execute('''
            INSERT INTO employees (name, position, department, basic_salary, doj, overtime_hours,
                                   bank_name, bank_account_number, ifsc_code, mobile_number, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (employee.name, employee.position, employee.department, employee.basic_salary, employee.doj,
              employee.overtime_hours, employee.bank_name, employee.bank_account_number,
              employee.ifsc_code, employee.mobile_number, employee.email))
        conn.commit()
        messagebox.showinfo("Success", "Employee added successfully.")
    except sqlite3.Error as e:
        messagebox.showerror("Error", str(e))

def fetch_employee_by_id(emp_id):
    cursor.execute('SELECT * FROM employees WHERE emp_id = ?', (emp_id,))
    row = cursor.fetchone()
    if row:
        emp_id, name, position, department, basic_salary, doj, overtime_hours, bank_name, \
        bank_account_number, ifsc_code, mobile_number, email = row
        return Employee(emp_id, name, position, department, basic_salary, doj, overtime_hours, bank_name,
                        bank_account_number, ifsc_code, mobile_number, email)
    return None

def fetch_all_employees():
    cursor.execute('SELECT * FROM employees')
    rows = cursor.fetchall()
    employees = []
    for row in rows:
        emp_id, name, position, department, basic_salary, doj, overtime_hours, bank_name, \
        bank_account_number, ifsc_code, mobile_number, email = row
        emp = Employee(emp_id, name, position, department, basic_salary, doj, overtime_hours, bank_name,
                       bank_account_number, ifsc_code, mobile_number, email)
        employees.append(emp)
    return employees


def update_employee(emp_id, new_employee_data):
    try:
        cursor.execute('''
            UPDATE employees
            SET name = ?, position = ?, department = ?, basic_salary = ?, doj = ?, overtime_hours = ?,
            bank_name = ?, bank_account_number = ?, ifsc_code = ?, mobile_number = ?, email = ?
            WHERE emp_id = ?
        ''', (new_employee_data['name'], new_employee_data['position'],
              new_employee_data['department'], new_employee_data['basic_salary'], new_employee_data['doj'],
              new_employee_data['overtime_hours'], new_employee_data['bank_name'],
              new_employee_data['bank_account_number'], new_employee_data['ifsc_code'],
              new_employee_data['mobile_number'], new_employee_data['email'], emp_id))
        conn.commit()
        messagebox.showinfo("Success", "Employee data updated successfully.")
    except sqlite3.Error as e:
        messagebox.showerror("Error", str(e))

def delete_employee_from_db(emp_id):
    try:
        cursor.execute('DELETE FROM employees WHERE emp_id = ?', (emp_id,))
        conn.commit()
        messagebox.showinfo("Success", "Employee deleted successfully.")
    except sqlite3.Error as e:
        messagebox.showerror("Error", str(e))

def calculate_net_salary(employee):
    total_allowances = sum(employee.allowances.values())
    total_deductions = sum(employee.deductions.values())
    overtime_pay = employee.overtime_hours * (employee.basic_salary / 173)
    net_salary = employee.basic_salary + overtime_pay + total_allowances - total_deductions
    return net_salary


def process_payroll():
    employees = fetch_all_employees()
    payroll_data = {}
    department_wise_salary = {}  # To store department-wise salary totals
    position_wise_salary = {}    # To store position-wise salary totals

    for emp in employees:
        net_salary = calculate_net_salary(emp)
        payroll_data[emp.emp_id] = net_salary

        # Accumulate salary based on department
        department = emp.department
        if department in department_wise_salary:
            department_wise_salary[department] += net_salary
        else:
            department_wise_salary[department] = net_salary

        # Accumulate salary based on position
        position = emp.position
        if position in position_wise_salary:
            position_wise_salary[position] += net_salary
        else:
            position_wise_salary[position] = net_salary

       # Create a single Figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1,2, figsize=(4,4))

    # Create department-wise salary bar chart
    departments = list(department_wise_salary.keys())
    department_salaries = list(department_wise_salary.values())

    ax1.bar(departments, department_salaries)
    ax1.set_xlabel("Departments")
    ax1.set_ylabel("Total Salary")
    ax1.set_title("Department-wise Salary Distribution")
    ax1.tick_params(axis='x', rotation=45)

    # Create position-wise salary bar chart
    positions = list(position_wise_salary.keys())
    position_salaries = list(position_wise_salary.values())

    ax2.bar(positions, position_salaries)
    ax2.set_xlabel("Positions")
    ax2.set_ylabel("Total Salary")
    ax2.set_title("Position-wise Salary Distribution")
    ax2.tick_params(axis='x', rotation=45)

    plt.tight_layout()
 

    chart_window = tk.Toplevel()
    chart_window.title("Payroll Analysis")
    chart_window.geometry("600x600")
    heading_label = tk.Label(chart_window, text="Analysis of Salary", font=("Helvetica", 16, "bold"))
    heading_label.pack(pady=10)
    payroll_canvas = FigureCanvasTkAgg(fig, chart_window)
    payroll_canvas.draw()
    payroll_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def close_chart_window():
        chart_window.destroy()
        
    def save_graphs():
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            fig.savefig(file_path, format="png")

    # Add a Download Graphs button to the chart window
    download_button = tk.Button(chart_window, text="Download Graphs", command=save_graphs,fg='BLACK' , bg='lightgreen')
    download_button.pack(pady=10)

    close_button = tk.Button(chart_window, text="Close", command=close_chart_window,fg='BLACK' , bg='red')
    close_button.pack(pady=10)

    return payroll_data
def display_employee_details(employee):
    message = (
        f"Employee ID: {employee.emp_id}\n"
        f"Name: {employee.name}\n"
        f"Position: {employee.position}\n"
        f"Department: {employee.department}\n"
        f"Basic Salary: {employee.basic_salary}\n"
        f"Date of Joining: {employee.doj}\n"
        f"Overtime Hours: {employee.overtime_hours}\n"
        f"Bank Name: {employee.bank_name}\n"
        f"Bank Account Number: {employee.bank_account_number}\n"
        f"IFSC Code: {employee.ifsc_code}\n"
        f"Mobile Number: {employee.mobile_number}\n"
        f"Email: {employee.email}\n"
        "Allowances:\n"
    )
    for allowance, amount in employee.allowances.items():
        message += f"  {allowance}: {amount}\n"
    message += "Deductions:\n"
    for deduction, amount in employee.deductions.items():
        message += f"  {deduction}: {amount}\n"
    messagebox.showinfo("Employee Details", message)

def display_all_employees(employee_records):
    custom_msgbox = tk.Toplevel()
    custom_msgbox.title("All Employees")
    custom_msgbox.configure(bg="light blue")
    
    
    heading_label = tk.Label(custom_msgbox, text="LIST OF ALL EMPLOYEES", font=("Helvetica", 16, "bold"), bg="light blue")
    heading_label.pack(pady=10)

    # Create a scrolledtext widget to display employee information
    employee_info_text = scrolledtext.ScrolledText(custom_msgbox, wrap=tk.WORD, bg="light blue", width=50, height=20)
    employee_info_text.pack(padx=10, pady=10)

    # Add content to the scrolledtext widget
    message = ""

    for emp in employee_records:
        message += (
            f"Employee ID: {emp.emp_id}\n"
            f"Name: {emp.name}\n"
            f"Position: {emp.position}\n"
            f"Department: {emp.department}\n"
            f"Basic Salary: {emp.basic_salary}\n"
            f"Date of Joining: {emp.doj}\n"
            f"Overtime Hours: {emp.overtime_hours}\n"
            f"Bank Name: {emp.bank_name}\n"
            f"Bank Account Number: {emp.bank_account_number}\n"
            f"IFSC Code: {emp.ifsc_code}\n"
            f"Mobile Number: {emp.mobile_number}\n"
            f"Email: {emp.email}\n"
            "=======================================\n"
        )
    employee_info_text.insert(tk.END, message)
    
    def save_to_pdf():
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            c = canvas.Canvas(file_path, pagesize=letter)
            c.setFont("Helvetica", 12)
            lines = message.split('\n')
            line_height = 15  # Adjust this value to change line spacing
            y = 750  # Starting position for the first line
            for line in lines:
                c.drawString(100, y, line)
                y -= line_height
            c.save()
            messagebox.showinfo("Save PDF", "list of all employee saved as PDF successfully!")


    download_button = tk.Button(custom_msgbox, text="Download PDF", command=save_to_pdf,fg='BLACK' , bg='lightgreen')
    download_button.pack(pady=10)
     
    def go_back_to_main_window():
        custom_msgbox.destroy()
        
        
    back_button = tk.Button(custom_msgbox, text="Back to Main Window", command=go_back_to_main_window,fg='BLACK' , bg='red')
    back_button.pack(pady=10)


def generate_payslip():
    emp_id = simpledialog.askinteger("Enter Employee ID", "Please enter the Employee ID:")
    if emp_id is not None:
        employee = fetch_employee_by_id(emp_id)
        if not employee:
            messagebox.showerror("Error", "Employee not found.")
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            payslip = f"Pay Slip - {current_date}\n"
            payslip += (
                f"Employee ID: {employee.emp_id}\n"
                f"Name: {employee.name}\n"
                f"Position: {employee.position}\n"
                f"Department: {employee.department}\n"
                f"Basic Salary: {employee.basic_salary}\n"
                f"Date of Joining: {employee.doj}\n"
                f"Overtime Hours: {employee.overtime_hours}\n"
                f"Bank Name: {employee.bank_name}\n"
                f"Bank Account Number: {employee.bank_account_number}\n"
                f"IFSC Code: {employee.ifsc_code}\n"
                f"Mobile Number: {employee.mobile_number}\n"
                f"Email: {employee.email}\n"
                "Allowances:\n"
            )
            for allowance, amount in employee.allowances.items():
                payslip += f"  {allowance}: {amount}\n"
            payslip += "Deductions:\n"
            for deduction, amount in employee.deductions.items():
                payslip += f"  {deduction}: {amount}\n"
            payslip += f"\nNet Salary: {calculate_net_salary(employee)}"
            custom_msgbox = tk.Toplevel()
            custom_msgbox.title("Employee Pay Slip")
            custom_msgbox.configure(bg="light blue")

            heading_label = tk.Label(custom_msgbox, text="PAYSTUBS", font=("Helvetica", 16, "bold"), bg="light blue")
            heading_label.pack(pady=10)

            payslip_label = tk.Label(custom_msgbox, text=payslip, bg="light blue", padx=10, pady=10)
            payslip_label.pack()
            def save_to_pdf():
                file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
                if file_path:
                    c = canvas.Canvas(file_path, pagesize=letter)
                    c.setFont("Helvetica", 12)
                    lines = payslip.split('\n')
                    line_height = 15  # Adjust this value to change line spacing
                    y = 750  # Starting position for the first line
                    for line in lines:
                        c.drawString(100, y, line)
                        y -= line_height
                    c.save()
                    messagebox.showinfo("Save PDF", "Payslip saved as PDF successfully!")
       

            download_button = tk.Button(custom_msgbox, text="Download PDF", command=save_to_pdf,fg='BLACK' , bg='lightgreen')
            download_button.pack(pady=10)
             
            def go_back_to_main_window():
                custom_msgbox.destroy()
                
                
            back_button = tk.Button(custom_msgbox, text="Back to Main Window", command=go_back_to_main_window,fg='BLACK' , bg='red')
            back_button.pack(pady=10)

                

def add_employee():
    
    def add_employee_submit():
        emp_id = emp_id_entry.get()
        name = name_entry.get()
        position = position_entry.get()
        department = department_entry.get()
        basic_salary = basic_salary_entry.get()
        doj = doj_entry.get()
        overtime_hours = overtime_hours_entry.get()
        bank_name = bank_name_entry.get()
        bank_account_number = bank_account_number_entry.get()
        ifsc_code = ifsc_code_entry.get()
        mobile_number = mobile_number_entry.get()
        email = email_entry.get()

        new_employee = Employee(emp_id, name, position, department, basic_salary, doj, overtime_hours,
                                bank_name, bank_account_number, ifsc_code, mobile_number, email)
        insert_employee(new_employee)
        add_employee_window.destroy()

    add_employee_window = tk.Toplevel()
    add_employee_window.title("Add Employee")
    add_employee_window.configure(bg="light blue")
    add_employee_window.geometry("400x1000")
    # Set the background color of the window
    heading_label = tk.Label(add_employee_window, text="Add Employee", bg="light blue", font=("Helvetica", 18, "bold"))
    heading_label.pack(pady=10)
 


    emp_id_label = tk.Label(add_employee_window, text="Employee ID:",fg='BLACK' , bg='lightyellow')
    emp_id_label.pack()
    emp_id_entry = tk.Entry(add_employee_window)
    emp_id_entry.pack(pady=5)

    name_label = tk.Label(add_employee_window, text="Name:" , fg='BLACK' , bg='lightyellow')
    name_label.pack()
    name_entry = tk.Entry(add_employee_window)
    name_entry.pack(pady=5)

    position_label = tk.Label(add_employee_window, text="Position:",fg='BLACK' , bg='lightyellow')
    position_label.pack()
    position_entry = tk.Entry(add_employee_window)
    position_entry.pack(pady=5)

    department_label = tk.Label(add_employee_window, text="Department:",fg='BLACK' , bg='lightyellow')
    department_label.pack()
    department_entry = tk.Entry(add_employee_window)
    department_entry.pack(pady=5)

    basic_salary_label = tk.Label(add_employee_window, text="Basic Salary:",fg='BLACK' , bg='lightyellow')
    basic_salary_label.pack()
    basic_salary_entry = tk.Entry(add_employee_window)
    basic_salary_entry.pack(pady=5)

    doj_label = tk.Label(add_employee_window, text="Date of Joining (YYYY-MM-DD):",fg='BLACK' , bg='lightyellow')
    doj_label.pack()
    doj_entry = tk.Entry(add_employee_window)
    doj_entry.pack(pady=5)

    overtime_hours_label = tk.Label(add_employee_window, text="Overtime Hours:",fg='BLACK' , bg='lightyellow')
    overtime_hours_label.pack()
    overtime_hours_entry = tk.Entry(add_employee_window)
    overtime_hours_entry.pack(pady=5)

    bank_name_label = tk.Label(add_employee_window, text="Bank Name:",fg='BLACK' , bg='lightyellow')
    bank_name_label.pack()
    bank_name_entry = tk.Entry(add_employee_window)
    bank_name_entry.pack(pady=5)

    bank_account_number_label = tk.Label(add_employee_window, text="Bank Account Number:",fg='BLACK' , bg='lightyellow')
    bank_account_number_label.pack()
    bank_account_number_entry = tk.Entry(add_employee_window)
    bank_account_number_entry.pack(pady=5)

    ifsc_code_label = tk.Label(add_employee_window, text="IFSC Code:",fg='BLACK' , bg='lightyellow')
    ifsc_code_label.pack()
    ifsc_code_entry = tk.Entry(add_employee_window)
    ifsc_code_entry.pack(pady=5)

    mobile_number_label = tk.Label(add_employee_window, text="Mobile Number:",fg='BLACK' , bg='lightyellow')
    mobile_number_label.pack()
    mobile_number_entry = tk.Entry(add_employee_window)
    mobile_number_entry.pack(pady=5)

    email_label = tk.Label(add_employee_window, text="Email:",fg='BLACK' , bg='lightyellow')
    email_label.pack()
    email_entry = tk.Entry(add_employee_window)
    email_entry.pack(pady=5)

    submit_button = tk.Button(add_employee_window, text="Add Employee", command=add_employee_submit,fg='BLACK' , bg='lightgreen')
    submit_button.pack(pady=5)
    
    def go_back_to_main_window():
        add_employee_window.destroy()
        
    back_button = tk.Button(add_employee_window, text="Back to Main Window", command=go_back_to_main_window,fg='BLACK' , bg='red')
    back_button.pack(pady=5)


                
def edit_employee():
        emp_id = simpledialog.askinteger("Enter Employee ID", "Please enter the Employee ID:")
        if emp_id is not None:
            employee = fetch_employee_by_id(emp_id)
            if not employee:
                messagebox.showerror("Error", "Employee not found.")
            else:
                def edit_employee_submit():
                    new_employee_data = {
                        'name': name_entry.get(),
                        'position': position_entry.get(),
                        'department': department_entry.get(),
                        'basic_salary': basic_salary_entry.get(),
                        'doj': doj_entry.get(),
                        'overtime_hours': overtime_hours_entry.get(),
                        'bank_name': bank_name_entry.get(),
                        'bank_account_number': bank_account_number_entry.get(),
                        'ifsc_code': ifsc_code_entry.get(),
                        'mobile_number': mobile_number_entry.get(),
                        'email': email_entry.get(),
                    }
                    update_employee(emp_id, new_employee_data)
                    
                edit_employee_window = tk.Toplevel()
                edit_employee_window.title("Edit Employee")
                edit_employee_window.configure(bg="light blue")
                edit_employee_window.geometry("400x1000")
                # Set the background color of the window
                heading_label = tk.Label(edit_employee_window, text="Edit Employee", bg="light blue", font=("Helvetica", 18, "bold"))
                heading_label.pack(pady=10)

                name_label = tk.Label(edit_employee_window, text="Name:",fg='BLACK' , bg='lightgreen')
                name_label.pack()
                name_entry = tk.Entry(edit_employee_window)
                name_entry.insert(tk.END, employee.name)
                name_entry.pack(pady=5)

                position_label = tk.Label(edit_employee_window, text="Position:",fg='BLACK' , bg='lightgreen')
                position_label.pack()
                position_entry = tk.Entry(edit_employee_window)
                position_entry.insert(tk.END, employee.position)
                position_entry.pack(pady=5)

                department_label = tk.Label(edit_employee_window, text="Department:",fg='BLACK' , bg='lightgreen')
                department_label.pack()
                department_entry = tk.Entry(edit_employee_window)
                department_entry.insert(tk.END, employee.department)
                department_entry.pack(pady=5)

                basic_salary_label = tk.Label(edit_employee_window, text="Basic Salary:",fg='BLACK' , bg='lightgreen')
                basic_salary_label.pack()
                basic_salary_entry = tk.Entry(edit_employee_window)
                basic_salary_entry.insert(tk.END, employee.basic_salary)
                basic_salary_entry.pack(pady=5)

                doj_label = tk.Label(edit_employee_window, text="Date of Joining (YYYY-MM-DD):",fg='BLACK' , bg='lightgreen')
                doj_label.pack()
                doj_entry = tk.Entry(edit_employee_window)
                doj_entry.insert(tk.END, employee.doj)
                doj_entry.pack(pady=5)

                overtime_hours_label = tk.Label(edit_employee_window, text="Overtime Hours:",fg='BLACK' , bg='lightgreen')
                overtime_hours_label.pack()
                overtime_hours_entry = tk.Entry(edit_employee_window)
                overtime_hours_entry.insert(tk.END, employee.overtime_hours)
                overtime_hours_entry.pack(pady=5)

                bank_name_label = tk.Label(edit_employee_window, text="Bank Name:",fg='BLACK' , bg='lightgreen')
                bank_name_label.pack()
                bank_name_entry = tk.Entry(edit_employee_window)
                bank_name_entry.insert(tk.END, employee.bank_name)
                bank_name_entry.pack(pady=5)

                bank_account_number_label = tk.Label(edit_employee_window, text="Bank Account Number:",fg='BLACK' , bg='lightgreen')
                bank_account_number_label.pack()
                bank_account_number_entry = tk.Entry(edit_employee_window)
                bank_account_number_entry.insert(tk.END, employee.bank_account_number)
                bank_account_number_entry.pack(pady=5)

                ifsc_code_label = tk.Label(edit_employee_window, text="IFSC Code:",fg='BLACK' , bg='lightgreen')
                ifsc_code_label.pack()
                ifsc_code_entry = tk.Entry(edit_employee_window)
                ifsc_code_entry.insert(tk.END, employee.ifsc_code)
                ifsc_code_entry.pack(pady=5)

                mobile_number_label = tk.Label(edit_employee_window, text="Mobile Number:",fg='BLACK' , bg='lightgreen')
                mobile_number_label.pack()
                mobile_number_entry = tk.Entry(edit_employee_window)
                mobile_number_entry.insert(tk.END, employee.mobile_number)
                mobile_number_entry.pack(pady=5)

                email_label = tk.Label(edit_employee_window, text="Email:",fg='BLACK' , bg='lightgreen')
                email_label.pack()
                email_entry = tk.Entry(edit_employee_window)
                email_entry.insert(tk.END, employee.email)
                email_entry.pack(pady=5)

                submit_button = tk.Button(edit_employee_window, text="Update Employee", command=edit_employee_submit,fg='BLACK' , bg='green')
                submit_button.pack(pady=5)
                def go_back_to_main_window():
                    edit_employee_window.destroy()
                    
                back_button = tk.Button(edit_employee_window, text="Back to Main Window", command=go_back_to_main_window,fg='BLACK' , bg='red')
                back_button.pack(pady=5)

def delete_employee():
    emp_id = simpledialog.askinteger("Enter Employee ID", "Please enter the Employee ID:")
    if emp_id is not None:
        employee = fetch_employee_by_id(emp_id)
        if not employee:
            messagebox.showerror("Error", "Employee not found.")
        else:
            result = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this employee?")
            if result:
                delete_employee_from_db(emp_id)

def main():
    create_employee_table()

    root = tk.Tk()
    root.title("Employee Payroll Management System")
    root.geometry("400x600")
    root.configure(bg="lightblue")  # Set the background color of the window
    var = tk.StringVar()
    HEAD_font = font.Font(family="ITALICS", size=15, weight="bold" ,)
    label = tk.Label(root, textvariable=var, bg="lightblue", bd="20", justify="right", padx=10, pady=20 , font=HEAD_font,fg="Darkblue")
    var.set("MSIT SERVICES.PVT.LTD")
    label.pack()
    
    button_font = font.Font(family="Helvetica", size=8, weight="bold")
    
    add_employee_btn = tk.Button(root, text="Add Employee", fg='BLACK' , bg='yellow' , command=add_employee, height=3, width=20,font=button_font)
    add_employee_btn.pack(pady=10)
    
    view_all_employees_btn = tk.Button(root, text="View All Employees",
                                       command=lambda: display_all_employees(fetch_all_employees()),height=3, width=20,font=button_font,fg='BLACK' , bg='pink')
    view_all_employees_btn.pack(pady=10)


    edit_employee_btn = tk.Button(root, text="Edit Employee", fg='BLACK' , bg='green' , command=edit_employee,height=3, width=20,font=button_font)
    edit_employee_btn.pack(pady=10)
    
    
    generate_payslip_btn = tk.Button(root, text="Generate Payslip",fg='BLACK' , bg='lightgreen' ,command=generate_payslip, height=3, width=20,font=button_font)
    generate_payslip_btn.pack(pady=10)

    delete_employee_btn = tk.Button(root, text="Delete Employee", fg='BLACK' , bg='red' ,command=delete_employee ,height=3, width=20,font=button_font)
    delete_employee_btn.pack(pady=10)
   
 
    process_payroll_btn = tk.Button(root, text="Payroll Analysis", command=process_payroll, height=3, width=20,font=button_font,fg='BLACK' , bg='grey')
    process_payroll_btn.pack(pady=10)

   

    def exit_application():
            root.destroy()
    
    exit_button = tk.Button(root, text="Exit", command=exit_application,height=3, width=20,font=button_font, fg='BLACK' , bg='red')
    exit_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
