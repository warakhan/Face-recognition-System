import face_recognition
import cv2
import numpy as np
import csv
import os
from datetime import datetime
import smtplib
from email.message import EmailMessage

# ------------------ Step 1: Choose Class ------------------
print("Select Class for Attendance:")
print("1. CSE-A")
print("2. CSE-B")
choice = input("Enter class (CSE-A or CSE-B): ").strip().upper()
class_name = choice if choice in ["CSE-A", "CSE-B"] else "CSE-A"
print(f"\n Starting attendance for: {class_name}\n")

# ------------------ Step 2: Load Students ------------------
students_file = f"classes/{class_name}.txt"

if not os.path.exists(students_file):
    print(f" Error: {students_file} not found!")
    exit()

with open(students_file, "r") as f:
    known_face_names = [line.strip() for line in f.readlines()]

known_face_encodings = []

# Load images from faces folder
for name in known_face_names:
    img_path = f"faces/{name.lower()}.jpg"
    if not os.path.exists(img_path):
        print(f" Face image not found for {name}: {img_path}")
        continue
    image = face_recognition.load_image_file(img_path)
    try:
        encoding = face_recognition.face_encodings(image)[0]
        known_face_encodings.append(encoding)
    except IndexError:
        print(f" No face found in image for {name}")
        continue

if not known_face_encodings:
    print(" No faces loaded. Exiting.")
    exit()

students = known_face_names.copy()

# ------------------ Step 3: Setup CSV File ------------------
current_date = datetime.now().strftime("%Y-%m-%d")
folder_path = os.path.join("attendance", class_name)
os.makedirs(folder_path, exist_ok=True)
filename = os.path.join(folder_path, f"{current_date}.csv")

with open(filename, "a", newline="") as f:
    lnwriter = csv.writer(f)
    # Write header only if file is empty
    if os.stat(filename).st_size == 0:
        lnwriter.writerow(["Name", "Login Time"])

    # ------------------ Step 4: Start Camera ------------------
    video_capture = cv2.VideoCapture(0)

    while True:
        _, frame = video_capture.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                name = known_face_names[best_match_index]

                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name + " Present", (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)

                if name in students:
                    students.remove(name)
                    current_time = datetime.now().strftime("%H:%M:%S")
                    lnwriter.writerow([name, current_time])
                    print(f" {name} marked present at {current_time}")

        cv2.imshow(f"{class_name} Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

# ------------------ Step 5: Clean Up ------------------
video_capture.release()
cv2.destroyAllWindows()
print("\n Attendance saved to:", filename)

# ------------------ Step 6: Email the Attendance File ------------------
sender_email = "warakhan1901@gmail.com"        # Replace with your Gmail
sender_password = "zpsc lckl tywg brsq"         # Use 16-char App Password
receiver_email = "warakhan86@gmail.com"       # Replace with faculty email

subject = f"Attendance Report - {class_name} - {current_date}"
body = f"""Dear Faculty,

Please find attached the attendance report for {class_name} dated {current_date}.

Regards,
Smart Attendance System
"""

msg = EmailMessage()
msg["From"] = sender_email
msg["To"] = receiver_email
msg["Subject"] = subject
msg.set_content(body)

# Attach CSV
with open(filename, "rb") as file:
    msg.add_attachment(file.read(), maintype="application", subtype="octet-stream", filename=os.path.basename(filename))

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)
        print("Attendance emailed successfully!")
except Exception as e:
    print(" Email failed:", e)
