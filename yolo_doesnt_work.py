import math
import pandas as pd
from ultralytics import YOLO
import cv2
import numpy as np

# Function to calculate angles between three points
def calculate_angle(pointA, pointB, pointC):
    if None in (pointA, pointB, pointC):
        return "Missing"
    AB = (pointB[0] - pointA[0], pointB[1] - pointA[1])
    BC = (pointC[0] - pointB[0], pointC[1] - pointB[1])
    dot_product = AB[0] * BC[0] + AB[1] * BC[1]
    magnitude_AB = math.sqrt(AB[0]**2 + AB[1]**2)
    magnitude_BC = math.sqrt(BC[0]**2 + BC[1]**2)
    if magnitude_AB == 0 or magnitude_BC == 0:
        return "Missing"
    angle = math.acos(dot_product / (magnitude_AB * magnitude_BC))
    return math.degrees(angle)

# Load YOLO model
model = YOLO("yolov8n-pose.pt")  # Replace with your YOLO pose model path

# Load the image or video
source = "test_video.mp4"  # Replace with your image or video file
cap = cv2.VideoCapture(source)

# Prepare to save keypoints and angles
keypoints_data = []
angles_data = []
frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Predict using YOLO model
    results = model.track(source=frame, conf=0.1, show=False, save=False)

    for result in results:
        if hasattr(result, 'keypoints') and result.keypoints is not None:
            raw_keypoints = result.keypoints.xy.cpu().numpy()  # Extract raw keypoints

            # Replace invalid keypoints ([0, 0]) with None
            valid_keypoints = [
                kp if not np.any(np.isclose(kp[:2], 0)) else [None, None, None]
                for kp in raw_keypoints
            ]
            valid_keypoints = np.array(valid_keypoints)

            # Debugging: Print valid keypoints
            print(f"Valid Keypoints (0–16): {valid_keypoints}")

            # Extract specific keypoints safely
            def get_point(index):
                if index < valid_keypoints.shape[0] and valid_keypoints[index][0] is not None:
                    return valid_keypoints[index][:2]
                return None

            nose = get_point(0)
            left_eye = get_point(1)
            right_eye = get_point(2)
            left_shoulder = get_point(5)
            right_shoulder = get_point(6)
            left_elbow = get_point(7)
            right_elbow = get_point(8)
            left_wrist = get_point(9)
            right_wrist = get_point(10)
            left_hip = get_point(11)
            right_hip = get_point(12)
            left_knee = get_point(13)
            right_knee = get_point(14)
            left_ankle = get_point(15)
            right_ankle = get_point(16)

            # Calculate angles only if enough keypoints are available
            head_angle = calculate_angle(left_eye, nose, right_eye)
            left_elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
            left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
            torso_angle = calculate_angle(left_hip, left_shoulder, right_shoulder)

            # Append angle data
            angles_data.append({
                "Frame": frame_count,
                "Head Angle": head_angle,
                "Left Elbow Angle": left_elbow_angle,
                "Right Elbow Angle": right_elbow_angle,
                "Left Knee Angle": left_knee_angle,
                "Right Knee Angle": right_knee_angle,
                "Torso Angle": torso_angle,
            })

            # Append keypoints for saving
            keypoints_dict = {
                "Frame": frame_count,
                **{f"Keypoint_{i}_X": kp[0] if kp[0] is not None else "Missing" for i, kp in enumerate(valid_keypoints)},
                **{f"Keypoint_{i}_Y": kp[1] if kp[1] is not None else "Missing" for i, kp in enumerate(valid_keypoints)},
                **{f"Keypoint_{i}_Conf": kp[2] if kp[2] is not None else "Missing" for i, kp in enumerate(valid_keypoints)},
            }
            keypoints_data.append(keypoints_dict)

    frame_count += 1

cap.release()

# Save results
if keypoints_data:
    pd.DataFrame(keypoints_data).to_csv("keypoints_with_angles.csv", index=False)
    print("Keypoints saved to keypoints_with_angles.csv")
else:
    print("No keypoints detected.")

if angles_data:
    pd.DataFrame(angles_data).to_csv("angles_with_head.csv", index=False)
    print("Angles saved to angles_with_head.csv")
else:
    print("No angles detected.")
