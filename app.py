import hashlib
import subprocess
import cv2
import numpy as np
import os
import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime
from threading import Timer
import time

# Load the Haar Cascade Classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Ensure the images directory exists
os.makedirs("images", exist_ok=True)

# Dummy data for ticket and verification status
ticket_status = {
    'example_hash': True  # Example hash with ticket status
}

verification_status = {
    'example_hash': True  # Example hash with verification status
}

recognized_hashes = set()  # Set to store recognized hashes
verified_no_ticket_hashes = set()  # Set to store verified hashes without ticket
last_activity_time = time.time()  # Track the last activity time

# Function to capture an image from the webcam
def capture_image():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video capture device.")
        return False

    root = tk.Tk()
    root.title("Image Capture")
    label = tk.Label(root)
    label.pack()
    
    frame = None
    ticket_available = False
    photo_taken = False

    def update_frame():
        nonlocal frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from video capture device.")
            return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        global last_activity_time
        last_activity_time = time.time()  # Update last activity time on each frame update
        
        for (x, y, w, h) in faces:
            face_img = frame[y:y+h, x:x+w]
            color = determine_color(photo_taken, ticket_available)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

        cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2_im)
        img_tk = ImageTk.PhotoImage(img)
        label.config(image=img_tk)
        label.image = img_tk
        root.update()

        root.after(1, update_frame)

    def determine_color(photo_taken, ticket_available):
        if ticket_available and photo_taken:
            return (0, 255, 0)  # Green if the user has a ticket
        elif photo_taken:
            return (0, 255, 255)  # Yellow if already recognized
        else:
            return (0, 0, 0)  # Black if not recognized

    def on_key_press(event):
        nonlocal ticket_available, photo_taken
        if event.keysym == 'c':  # Press 'c' to save the image and process the hash
            if frame is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                for i, (x, y, w, h) in enumerate(faces):
                    face_img = frame[y:y+h, x:x+w]
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    face_path = f"images/face_{timestamp}_{i}.jpg"
                    cv2.imwrite(face_path, face_img)
                    
                    image_hash = generate_image_hash(face_path)
                    if image_hash and not has_been_recognized(image_hash):
                        hash_file_path = f"images/hash_{timestamp}_{i}.txt"
                        save_hash_to_file(image_hash, hash_file_path)
                        call_node_script(hash_file_path)
                        recognized_hashes.add(image_hash)
                        Timer(10.0, turn_yellow, [image_hash]).start()
        elif event.keysym == 't':  # Press 't' to indicate ticket availability
            if photo_taken:
                ticket_available = True
                print("Ticket purchased. Color will be updated to green.")
            else:
                print("You must take a photo first by pressing 'y' before buying a ticket.")
        elif event.keysym == 'y':  # Press 'y' to turn the frame yellow
            if frame is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                for i, (x, y, w, h) in enumerate(faces):
                    face_img = frame[y:y+h, x:x+w]
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    face_path = f"images/face_{timestamp}_{i}.jpg"
                    cv2.imwrite(face_path, face_img)
                    
                    image_hash = generate_image_hash(face_path)
                    if image_hash:
                        turn_yellow(image_hash)
                        photo_taken = True
                        print("Photo taken. Color will be yellow until ticket is purchased.")
        elif event.keysym == 'x':  # Press 'x' to cancel the ticket purchase and refund money
            ticket_available = False
            print("Ticket purchase cancelled. Money refunded.")
        elif event.keysym == 'q':  # Press 'q' to quit
            root.destroy()

    def turn_yellow(image_hash):
        if user_is_verified(image_hash) and not user_has_ticket(image_hash):
            verified_no_ticket_hashes.add(image_hash)
        print(f"Hash {image_hash} color turned to yellow.")

    def check_inactivity():
        global last_activity_time
        current_time = time.time()
        if current_time - last_activity_time > 600:  # 10 minutes inactivity
            update_colors_for_verified_no_ticket()
            verified_no_ticket_hashes.clear()  # Clear the list after processing
        root.after(30000, check_inactivity)  # Schedule the next check in 30 seconds

    def update_colors_for_verified_no_ticket():
        nonlocal frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from video capture device.")
            return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        for (x, y, w, h) in faces:
            face_img = frame[y:y+h, x:x+w]
            face_path = f"temp_face_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            cv2.imwrite(face_path, face_img)
            
            # Generate hash from the face image
            image_hash = generate_image_hash(face_path)
            if image_hash in verified_no_ticket_hashes:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)  # Yellow color

        cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2_im)
        img_tk = ImageTk.PhotoImage(img)
        label.config(image=img_tk)
        label.image = img_tk
        root.update()

    def close_camera():
        cap.release()
        print("Camera released.")

    root.bind("<KeyPress>", on_key_press)
    update_frame()
    root.after(30000, check_inactivity)  # Start the inactivity check
    root.mainloop()
    return True

# Function to read and preprocess the image
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Failed to load image from {image_path}.")
        return None
    
    img = cv2.resize(img, (96, 96))
    img = img[..., ::-1]  # BGR to RGB
    img = np.around(np.transpose(img, (2, 0, 1)) / 255.0, decimals=12)
    img = np.array([img])
    return img

# Function to generate hash from image
def generate_image_hash(image_path):
    img = preprocess_image(image_path)
    if img is None:
        print("Error: Preprocessing failed. Exiting.")
        return None
    
    encoding_str = ','.join(map(str, img.flatten()))
    hash_value = hashlib.sha256(encoding_str.encode()).hexdigest()
    return hash_value

# Function to save the hash to a file
def save_hash_to_file(hash_value, file_path):
    with open(file_path, 'w') as f:
        f.write(hash_value)
    print(f"Hash written to {file_path}")

# Function to call the Node.js script with the hash file path as an argument
def call_node_script(hash_file_path):
    try:
        result = subprocess.run(['node', 'Interaction.js', hash_file_path], capture_output=True, text=True)
        print("Node.js script output:", result.stdout)
        print("Node.js script error (if any):", result.stderr)
    except Exception as e:
        print(f"Error: Failed to call Node.js script. {str(e)}")

# Function to check if the user has a ticket
def user_has_ticket(image_hash):
    return ticket_status.get(image_hash, False)

# Function to check if the user is verified
def user_is_verified(image_hash):
    return verification_status.get(image_hash, False)

# Function to check if the image hash has been recognized
def has_been_recognized(image_hash):
    return image_hash in recognized_hashes

# Function to update the ticket status and verification status
def update_ticket_and_verification_status(image_hash, has_ticket, is_verified):
    ticket_status[image_hash] = has_ticket
    verification_status[image_hash] = is_verified

# Main function
def main():
    if not capture_image():
        print("Error: Image capture failed. Exiting.")
        return

    print("Image capture and processing completed successfully.")

if __name__ == "__main__":
    main()
