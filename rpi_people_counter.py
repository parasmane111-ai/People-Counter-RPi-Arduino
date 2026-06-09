import cv2
from ultralytics import YOLO
from collections import defaultdict
import serial
import time

# ---------------- STARTUP DELAY ----------------
time.sleep(15)

# ---------------- USB SERIAL SETUP ----------------
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)   # Arduino resets when serial opens

# ---------------- YOLO SETUP ----------------
model = YOLO("/home/pi/people_counter/yolov8n.pt")

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

WIDTH = 640
HEIGHT = 480

line_y = HEIGHT // 2
offset = 25

# ---------------- COUNTERS ----------------
in_count = 0
out_count = 0
total_inside = 0

track_history = defaultdict(list)
counted_ids = set()

last_sent_value = -1

# ---------------- MAIN LOOP ----------------
while True:

    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (WIDTH, HEIGHT))

    results = model.track(
        frame,
        persist=True,
        classes=[0],
        imgsz=320,
        conf=0.5,
        tracker="bytetrack.yaml",
        verbose=False
    )

    if results[0].boxes.id is not None:

        boxes = results[0].boxes.xyxy.cpu()
        ids = results[0].boxes.id.cpu()

        for box, track_id in zip(boxes, ids):

            track_id = int(track_id)

            x1, y1, x2, y2 = map(int, box)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

            track_history[track_id].append(cy)

            if len(track_history[track_id]) > 20:
                track_history[track_id].pop(0)

            if track_id not in counted_ids and len(track_history[track_id]) > 5:

                first = track_history[track_id][0]
                last = track_history[track_id][-1]

                # OUTSIDE -> INSIDE
                if first < line_y - offset and last > line_y + offset:
                    in_count += 1
                    total_inside += 1
                    counted_ids.add(track_id)

                # INSIDE -> OUTSIDE
                elif first > line_y + offset and last < line_y - offset:
                    out_count += 1
                    total_inside -= 1
                    counted_ids.add(track_id)

    # ---------------- SEND TO ARDUINO ----------------
    if total_inside != last_sent_value:
        ser.write((str(total_inside) + "\n").encode())
        print("Sent:", total_inside)
        last_sent_value = total_inside

    # ---------------- DISPLAY WINDOW ----------------
    cv2.line(frame, (0, line_y), (WIDTH, line_y), (255, 0, 0), 3)

    cv2.putText(frame, f"IN: {in_count}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.putText(frame, f"OUT: {out_count}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.putText(frame, f"INSIDE: {total_inside}", (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    cv2.imshow("People Counter", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

# ---------------- CLEANUP ----------------
cap.release()
cv2.destroyAllWindows()
ser.close()
