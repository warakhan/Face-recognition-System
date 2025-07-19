import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import cv2
import face_recognition
import numpy as np
import csv
from datetime import datetime
import os
import smtplib
import itertools
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Setup
known_face_encodings = []
known_face_names = []
attendance_record = {}
current_date = datetime.now().strftime("%Y-%m-%d")
filename = f"{current_date}.csv"
theme = "light"
cap = None
glow_colors = itertools.cycle(["#00ffff", "#00e5ff", "#00ccff", "#00bfff", "#00aaff"])

# Theme colors
bg_colors = {"light": "#f0f8ff", "dark": "#1e1e1e"}
fg_colors = {"light": "#000000", "dark": "#ffffff"}
btn_colors = {"light": "#007bff", "dark": "#00bfff"}

# Load faces
def load_known_faces(selected_class):
    known_face_encodings.clear()
    known_face_names.clear()
    folder = "faces"
    class_file = f"classes/{selected_class}.txt"
    if not os.path.exists(class_file):
        return
    with open(class_file, "r") as f:
        student_names = [line.strip() for line in f.readlines()]
    for name in student_names:
        file_path = os.path.join(folder, f"{name.lower()}.jpg")
        if os.path.exists(file_path):
            image = face_recognition.load_image_file(file_path)
            encoding = face_recognition.face_encodings(image)[0]
            known_face_encodings.append(encoding)
            known_face_names.append(name)

# GUI setup
root = tk.Tk()
root.title("Smart Attendance System")
root.geometry("1000x700")

canvas = tk.Canvas(root)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Apply theme
def apply_theme():
    root.configure(bg=bg_colors[theme])
    scrollable_frame.configure(bg=bg_colors[theme])
    label.config(bg=bg_colors[theme], fg=fg_colors[theme])
    video_label.config(bg=bg_colors[theme])
    class_label.config(bg=bg_colors[theme], fg=fg_colors[theme])
    for btn in [btn_start, btn_stop, btn_email, btn_theme, btn_register]:
        btn.config(bg=btn_colors[theme], fg="white", activebackground="#0056b3")

def toggle_theme():
    global theme
    theme = "dark" if theme == "light" else "light"
    apply_theme()

label = tk.Label(scrollable_frame, text="Live Attendance System", font=("Helvetica", 20, "bold"))
label.pack(pady=10)

class_label = tk.Label(scrollable_frame, text="Select Class:", font=("Helvetica", 12))
class_label.pack()

selected_class = tk.StringVar()
class_dropdown = ttk.Combobox(scrollable_frame, textvariable=selected_class, values=["CSE-A", "CSE-B"], state="readonly")
class_dropdown.pack(pady=5)
class_dropdown.current(0)

video_label = tk.Label(scrollable_frame)
video_label.pack()

def mark_attendance(name):
    current_time = datetime.now().strftime("%H:%M:%S")
    if name not in attendance_record:
        attendance_record[name] = [current_date, current_time, current_time]
    else:
        attendance_record[name][2] = current_time

def update_frame():
    global cap
    ret, frame = cap.read()
    if not ret:
        return
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        face_distance = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distance)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            mark_attendance(name)
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name + " Present", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)
    root.after(10, update_frame)

def start_attendance():
    global cap
    load_known_faces(selected_class.get())
    cap = cv2.VideoCapture(0)
    update_frame()

def stop_attendance():
    global cap
    if cap:
        cap.release()
    save_csv()
    present = list(attendance_record.keys())
    absent = []
    class_file = f"classes/{selected_class.get()}.txt"
    if os.path.exists(class_file):
        with open(class_file, "r") as f:
            all_students = [line.strip() for line in f.readlines()]
        absent = [name for name in all_students if name not in present]
    msg = f"Attendance saved.\nPresent: {len(present)}\nAbsent: {len(absent)}"
    if absent:
        msg += "\nAbsent: " + ", ".join(absent)
    messagebox.showinfo("Done", msg)

def save_csv():
    class_name = selected_class.get()
    folder_path = os.path.join("attendance", class_name)
    os.makedirs(folder_path, exist_ok=True)
    full_path = os.path.join(folder_path, f"{current_date}.csv")
    existing_data = {}
    if os.path.exists(full_path):
        with open(full_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data[row["Name"]] = row
    for name in attendance_record:
        date, login, logout = attendance_record[name]
        existing_data[name] = {"Name": name, "Date": date, "Login Time": login, "Logout Time": logout, "Status": "Present"}
    with open(full_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "Date", "Login Time", "Logout Time", "Status"])
        writer.writeheader()
        for row in existing_data.values():
            writer.writerow(row)

def send_email():
    sender_email = "ammarkhan8217@gmail.com"
    sender_password = "zpsc lckl tywg brsq"
    recipients = ["warakhan86@gmail.com"]
    subject = "Daily Attendance Report"
    body = f"Hi,\n\nAttached is the attendance sheet for {current_date}."
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    folder_path = os.path.join("attendance", selected_class.get())
    full_path = os.path.join(folder_path, f"{current_date}.csv")
    with open(full_path, "rb") as file:
        part = MIMEApplication(file.read(), Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        msg.attach(part)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        messagebox.showinfo("Success", "Email sent successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send email:\n{e}")

def register_student():
    name = simpledialog.askstring("Student Name", "Enter Student Name:")
    if not name:
        messagebox.showwarning("Input Error", "Name is required.")
        return
    section_input = simpledialog.askstring("Section", "Enter Section (e.g., CSE-A):")
    if not section_input:
        messagebox.showwarning("Input Error", "Section is required.")
        return
    section = section_input.strip().upper().replace(" ", "")
    if section not in ["CSE-A", "CSE-B"]:
        messagebox.showerror("Error", "Invalid section. Use CSE-A or CSE-B.")
        return
    class_file = f"classes/{section}.txt"
    os.makedirs("faces", exist_ok=True)
    cap = cv2.VideoCapture(0)
    messagebox.showinfo("Face Capture", "Look straight into the camera. Face will be captured automatically.")
    captured = False
    while True:
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Camera Error", "Cannot access camera.")
            break
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.imshow("Registering Face", frame)
        if face_locations and not captured:
            filename = f"faces/{name.lower()}.jpg"
            cv2.imwrite(filename, frame)
            captured = True
            messagebox.showinfo("Success", f"Face captured and saved for {name}.")
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    if not os.path.exists(class_file):
        open(class_file, "w").close()
    with open(class_file, "r") as f:
        existing_names = [line.strip().lower() for line in f.readlines()]
    if name.lower() not in existing_names:
        with open(class_file, "a") as f:
            f.write(name + "\n")
        messagebox.showinfo("Registration Complete", f"{name} added to {section}.")
    else:
        messagebox.showinfo("Already Exists", f"{name} is already registered in {section}.")

def animate_label():
    label.config(fg=next(glow_colors))
    root.after(200, animate_label)

btn_frame = tk.Frame(scrollable_frame)
btn_frame.pack(pady=20)

btn_start = tk.Button(btn_frame, text="▶ Start Attendance", font=("Helvetica", 12), width=20, height=2, command=start_attendance)
btn_start.grid(row=0, column=0, padx=10)

btn_stop = tk.Button(btn_frame, text="💾 Stop & Save", font=("Helvetica", 12), width=20, height=2, command=stop_attendance)
btn_stop.grid(row=0, column=1, padx=10)

btn_email = tk.Button(btn_frame, text="📤 Send Email", font=("Helvetica", 12), width=20, height=2, command=send_email)
btn_email.grid(row=1, column=0, pady=10)

btn_theme = tk.Button(btn_frame, text="🎨 Toggle Theme", font=("Helvetica", 12), width=20, height=2, command=toggle_theme)
btn_theme.grid(row=1, column=1, pady=10)

btn_register = tk.Button(btn_frame, text="📝 Register Student", font=("Helvetica", 12), width=20, height=2, command=register_student)
btn_register.grid(row=2, column=0, pady=10)

apply_theme()
animate_label()
root.mainloop()