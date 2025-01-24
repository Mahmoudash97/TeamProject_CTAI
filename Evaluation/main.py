import sys
import os
import subprocess
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib
import matplotlib.pyplot as plt

# Step 1: Pre-trained Model Path
model_path = "/mnt/c/Users/asadi/Desktop/TeamProject_CTAI/Evaluation/2athlete_scoring_model_new (1).pkl"  # Replace with your model file

# Step 2: Process Video with Sports2D
def process_video_with_sports2d(video_path):
    """
    Process the video using Sports2D CLI.
    """
    try:
        # Convert to absolute path
        video_path = os.path.abspath(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = f"{video_name}_Sports2D"

        # Ensure the video file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Use the sports2d CLI command directly
        cmd = (
            f"sports2d "
            f"--save_vid false --save_img false --save_pose false "
            f"--show_graphs false --multiperson true --keypoint_likelihood_threshold 0.65 "
            f"--video_input {video_path}"
        )

        print(f"Running command: {cmd}")
        subprocess.run(cmd, shell=True, check=True)
        print("Sports2D processing completed successfully.")

        # Return the output directory
        return output_dir
    except FileNotFoundError as fnfe:
        print(f"File Error: {fnfe}")
        raise
    except subprocess.CalledProcessError as cpe:
        print(f"Error running Sports2D: {cpe}")
        print(f"Return Code: {cpe.returncode}")
        raise


# Step 3: Locate and Load .mot Files for person00 and person01
def load_person_mot_files(output_dir):
    """
    Locate and load .mot files for person00 and person01 in the output directory.
    """
    try:
        # Find all .mot files in the output directory
        mot_files = [f for f in os.listdir(output_dir) if f.endswith(".mot")]

        # Filter only person00 and person01
        filtered_files = [f for f in mot_files if "person00" in f or "person01" in f]

        if not filtered_files:
            raise FileNotFoundError("No .mot files for person00 or person01 found.")

        print(f"Filtered .mot files: {filtered_files}")
        return filtered_files
    except Exception as e:
        print(f"Error locating .mot files: {e}")
        raise

# Step 4: Score Each Person and Provide Feedback
def score_person(mot_file_path, model_path):
    """
    Score a single person's .mot file and provide feedback.
    """
    try:
        # Extract the person ID from the file name
        person_id = mot_file_path.split('_')[-1].replace('.mot', '')

        # Load the .mot file into a DataFrame
        df = pd.read_csv(mot_file_path, sep="\t", engine="python", skiprows=10)
        df = df.drop(columns=['time'], errors='ignore')  # Drop 'time' column if it exists

        # Normalize the data
        scaler = MinMaxScaler()
        df = df.transform(lambda x: (x - x.min()) / (x.max() - x.min()))

        # Load the pre-trained model
        model = joblib.load(model_path)
        print(f"Model loaded successfully for {person_id}")

        # Predict scores
        predictions = model.predict(df)
        overall_score = predictions.mean()

        # Generate feedback
        manual_weights = {
            'trunk': 7.0, 'pelvis': 7.0, 'shoulders': 6.5, 'head': 6.0,
            'right arm': 6.2, 'left arm': 6.2, 'right forearm': 6.5, 'left forearm': 6.5,
            'right hip': 6.8, 'left hip': 6.8, 'right knee': 6.5, 'left knee': 6.5,
            'right ankle': 6.0, 'left ankle': 6.0, 'right thigh': 6.5, 'left thigh': 6.5,
            'right shank': 5.5, 'left shank': 5.5, 'right foot': 5.0, 'left foot': 5.0
        }
        weights = pd.Series(manual_weights).reindex(df.columns).fillna(1.0)

        # Calculate feature contributions
        feature_contributions = df.apply(lambda row: row * weights, axis=1).mean()

        # Identify the weakest features
        low_contribution_features = feature_contributions.nsmallest(3)

        feedback = []
        for feature in low_contribution_features.index:
            feedback.append(f"The athlete needs to improve {feature.replace('_', ' ')} to achieve better results.")

        # Return results
        return person_id, overall_score, feedback
    except Exception as e:
        print(f"Error scoring {mot_file_path}: {e}")
        raise

# Step 5: Automate the Entire Process
def automate_scoring(video_path):
    """
    Fully automate the process for video processing, scoring, and feedback for person00 and person01.
    """
    # Process video with Sports2D
    output_dir = process_video_with_sports2d(video_path)

    # Locate .mot files for person00 and person01
    mot_files = load_person_mot_files(output_dir)

    # Score each person
    scores = []
    for mot_file in mot_files:
        mot_file_path = os.path.join(output_dir, mot_file)
        person_id, score, feedback = score_person(mot_file_path, model_path)
        scores.append((person_id, score, feedback))

    # Display overall results
    print("\nFinal Results:")
    for person_id, score, feedback in scores:
        print(f"{person_id}: {score:.2f} / 5.0")
        for line in feedback:
            print(f"  - {line}")

    # Visualization
    person_ids = [s[0] for s in scores]
    overall_scores = [s[1] for s in scores]

    plt.figure(figsize=(10, 6))
    plt.bar(person_ids, overall_scores, color='skyblue')
    plt.ylim(0, 5)
    plt.xlabel('Person ID')
    plt.ylabel('Overall Score (0-5)')
    plt.title('Overall Scores for person00 and person01')
    plt.xticks(rotation=90)
    plt.show()

# Main Entry Point
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <video_path>")
        sys.exit(1)

    # Get the video path from command-line arguments
    video_path = sys.argv[1]

    # Check if the provided path is valid
    if not os.path.exists(video_path):
        print(f"Error: The video file does not exist at path {video_path}")
        sys.exit(1)

    print(f"Evaluating video: {video_path}")
    automate_scoring(video_path)
