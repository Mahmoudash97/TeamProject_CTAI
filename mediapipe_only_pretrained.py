import math
import cv2
import mediapipe as mp
import pandas as pd

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose()

# Function to calculate the angle between three points
def calculate_angle(a, b, c):
    """Calculate the angle between three points."""
    a = [a.x, a.y]
    b = [b.x, b.y]
    c = [c.x, c.y]

    ab = [b[0] - a[0], b[1] - a[1]]
    bc = [c[0] - b[0], c[1] - b[1]]

    dot_product = ab[0] * bc[0] + ab[1] * bc[1]
    magnitude_ab = math.sqrt(ab[0]**2 + ab[1]**2)
    magnitude_bc = math.sqrt(bc[0]**2 + bc[1]**2)

    if magnitude_ab == 0 or magnitude_bc == 0:  # Avoid division by zero
        return 0

    angle = math.acos(dot_product / (magnitude_ab * magnitude_bc))
    return math.degrees(angle)

# Load video source
cap = cv2.VideoCapture("test_video.mp4")  # Replace with your video file

# Get video properties for saving the output
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))
output_path = "evaluated_video.avi"
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec for AVI files
out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

# Data collection
angles_data = []

frame_count = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert the frame to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        # Draw the pose landmarks on the frame
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
        )

        # Calculate important angles
        try:
            left_elbow_angle = calculate_angle(landmarks[11], landmarks[13], landmarks[15])  # Shoulder -> Elbow -> Wrist
            right_elbow_angle = calculate_angle(landmarks[12], landmarks[14], landmarks[16])
            left_knee_angle = calculate_angle(landmarks[23], landmarks[25], landmarks[27])  # Hip -> Knee -> Ankle
            right_knee_angle = calculate_angle(landmarks[24], landmarks[26], landmarks[28])
            torso_angle = calculate_angle(landmarks[23], landmarks[11], landmarks[12])  # Left Hip -> Left Shoulder -> Right Shoulder
            left_ankle_angle = calculate_angle(landmarks[25], landmarks[27], landmarks[31])  # Knee -> Ankle -> Foot
            right_ankle_angle = calculate_angle(landmarks[26], landmarks[28], landmarks[32])

            # Append data for CSV
            angles_data.append({
                "Frame": frame_count,
                "Left Elbow Angle": left_elbow_angle,
                "Right Elbow Angle": right_elbow_angle,
                "Left Knee Angle": left_knee_angle,
                "Right Knee Angle": right_knee_angle,
                "Torso Angle": torso_angle,
                "Left Ankle Angle": left_ankle_angle,
                "Right Ankle Angle": right_ankle_angle
            })

            # Visualize angles on the frame
            cv2.putText(frame, f"Left Elbow: {int(left_elbow_angle)}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f"Right Elbow: {int(right_elbow_angle)}", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f"Left Knee: {int(left_knee_angle)}", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f"Right Knee: {int(right_knee_angle)}", (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f"Torso: {int(torso_angle)}", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        except:
            print("Error calculating angles for this frame.")

    # Write the processed frame to the output video
    out.write(frame)

    # Display the frame in real-time
    cv2.imshow("Pose Estimation", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_count += 1

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()

# Save angles to a CSV file
angles_df = pd.DataFrame(angles_data)
angles_df.to_csv("athletic_angles.csv", index=False)

print("Video saved to", output_path)
print("Angles saved to athletic_angles.csv")
