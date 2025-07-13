import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fpdf import FPDF

# GUI setup
root = tk.Tk()
root.title("Attendance Dashboard")
root.geometry("950x650")

# ----- FUNCTIONS -----
def get_class_list():
    return [f.replace(".txt", "") for f in os.listdir("classes") if f.endswith(".txt")]

def load_attendance(file_path):
    try:
        with open(file_path, "r") as file:
            reader = csv.DictReader(file)
            return list(reader)
    except FileNotFoundError:
        messagebox.showerror("Error", f"File not found:\n{file_path}")
        return []
    except Exception as e:
        messagebox.showerror("Error", f"Error reading file:\n{e}")
        return []

def show_attendance():
    selected_class = class_var.get()
    selected_date = cal.get_date().strftime("%Y-%m-%d")
    file_path = f"attendance/{selected_class}/{selected_date}.csv"

    # Load student list
    try:
        with open(f"classes/{selected_class}.txt", "r") as f:
            class_students = [line.strip() for line in f if line.strip()]
    except:
        messagebox.showerror("Error", f"Could not load students list for {selected_class}")
        return

    # Load attendance
    records = load_attendance(file_path)

    # Clear previous table
    for row in tree.get_children():
        tree.delete(row)

    present_students = []
    absent_students = []

    for rec in records:
        name = rec.get('Name', '').strip()
        date = rec.get('Date', '')
        login = rec.get('Login Time', '')
        logout = rec.get('Logout Time', '')

        if name in class_students:
            tree.insert("", "end", values=(name, date, login, logout))
            if login:
                present_students.append(name)

    absent_students = [s for s in class_students if s not in present_students]

    draw_chart(len(present_students), len(absent_students), absent_students)
    status_label.config(text=f"📅 {selected_date} | ✅ Present: {len(present_students)} | ❌ Absent: {len(absent_students)}")

def draw_chart(present_count, absent_count, absent_students):
    for widget in right_frame.winfo_children():
        widget.destroy()

    fig = plt.Figure(figsize=(4.5, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.pie(
        [present_count, absent_count],
        labels=["Present", "Absent"],
        autopct="%1.1f%%",
        colors=["#4CAF50", "#F44336"],
        startangle=90
    )
    ax.set_title("Attendance Distribution")

    if absent_students:
        absent_text = "Absent:\n" + "\n".join(absent_students)
        fig.text(0.02, 0.01, absent_text, fontsize=8, verticalalignment='bottom')

    chart_canvas = FigureCanvasTkAgg(fig, master=right_frame)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack()

def export_pdf():
    selected_class = class_var.get()
    selected_date = cal.get_date().strftime("%Y-%m-%d")
    file_path = f"attendance/{selected_class}/{selected_date}.csv"
    records = load_attendance(file_path)

    if not records:
        messagebox.showinfo("No Data", "No attendance data to export.")
        return

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=f"Attendance Report: {selected_class} - {selected_date}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(5)

    pdf.set_fill_color(200, 220, 255)
    pdf.cell(50, 8, "Name", 1, 0, 'C', 1)
    pdf.cell(40, 8, "Date", 1, 0, 'C', 1)
    pdf.cell(50, 8, "Login Time", 1, 0, 'C', 1)
    pdf.cell(50, 8, "Logout Time", 1, 1, 'C', 1)

    for rec in records:
        pdf.cell(50, 8, rec['Name'], 1)
        pdf.cell(40, 8, rec.get("Date", ""), 1)
        pdf.cell(50, 8, rec.get("Login Time", ""), 1)
        pdf.cell(50, 8, rec.get("Logout Time", ""), 1, 1)

    out_name = f"Attendance_{selected_class}_{selected_date}.pdf"
    pdf.output(out_name)
    messagebox.showinfo("Exported", f"PDF saved as {out_name}")

# ----- UI LAYOUT -----
top_frame = tk.Frame(root)
top_frame.pack(pady=10)

class_var = tk.StringVar()
class_dropdown = ttk.Combobox(top_frame, textvariable=class_var, state="readonly")
class_dropdown['values'] = get_class_list()
class_dropdown.current(0)
class_dropdown.grid(row=0, column=0, padx=10)

cal = DateEntry(top_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
cal.grid(row=0, column=1, padx=10)

btn = tk.Button(top_frame, text="📊 Show Attendance", command=show_attendance)
btn.grid(row=0, column=2, padx=10)

btn_export = tk.Button(top_frame, text="📤 Export PDF", command=export_pdf)
btn_export.grid(row=0, column=3, padx=10)

status_label = tk.Label(root, text="", font=("Arial", 12))
status_label.pack(pady=5)

middle_frame = tk.Frame(root)
middle_frame.pack(padx=20, fill=tk.BOTH, expand=True)

tree = ttk.Treeview(middle_frame, columns=("Name", "Date", "Login", "Logout"), show="headings")
tree.heading("Name", text="Name")
tree.heading("Date", text="Date")
tree.heading("Login", text="Login Time")
tree.heading("Logout", text="Logout Time")
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(middle_frame, orient="vertical", command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

right_frame = tk.Frame(root)
right_frame.pack(pady=10)

root.mainloop()
