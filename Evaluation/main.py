import sys
import os
import subprocess
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Pre-trained Model Path
model_path = "/mnt/c/Users/asadi/Desktop/TeamProject_CTAI/Evaluation/2athlete_scoring_model_new (1).pkl"

# Process Video with Sports2D
def process_video_with_sports2d(video_path):
    """
    Process the video using Sports2D CLI.
    """
    try:
        video_path = os.path.abspath(video_path)
        output_dir = f"{os.path.splitext(os.path.basename(video_path))[0]}_Sports2D"

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cmd = (
            f"sports2d "
            f"--save_vid false --save_img false --save_pose false "
            f"--show_graphs false --multiperson true --keypoint_likelihood_threshold 0.65 "
            f"--video_input {video_path}"
        )
        print(f"Running command: {cmd}")
        subprocess.run(cmd, shell=True, check=True)
        print("Sports2D processing completed successfully.")
        return output_dir
    except subprocess.CalledProcessError as cpe:
        print(f"Error running Sports2D: {cpe}")
        raise

# Load and Score .mot File
def score_video_mot_file(output_dir, model_path):
    """
    Locate and score the .mot file for the uploaded video.
    """
    try:
        mot_files = [f for f in os.listdir(output_dir) if f.endswith(".mot")]

        if not mot_files:
            raise FileNotFoundError("No .mot files found in the output directory.")

        # Process the first .mot file (assuming one video corresponds to one .mot file)
        mot_file_path = os.path.join(output_dir, mot_files[0])
        print(f"Processing MOT file: {mot_file_path}")

        # Load .mot file into DataFrame
        df = pd.read_csv(mot_file_path, sep="\t", engine="python", skiprows=10)
        print("First few rows of the .mot file:")
        print(df.head())

        df = df.drop(columns=['time'], errors='ignore')  # Drop 'time' column if it exists

        # Normalize the data
        scaler = MinMaxScaler()
        df = pd.DataFrame(scaler.fit_transform(df), columns=df.columns)

        print("Scaled columns:")
        print(df.columns)

        # Load pre-trained model
        model = joblib.load(model_path)
        print("Model loaded successfully.")

        # Predict scores
        predictions = model.predict(df)
        print("Predictions:")
        print(predictions)

        overall_score = predictions.mean()

        # Generate feedback based on low contribution features (you can modify this)
        manual_weights = {
            'trunk': 7.0, 'pelvis': 7.0, 'shoulders': 6.5, 'head': 6.0,
            'right arm': 6.2, 'left arm': 6.2, 'right forearm': 6.5, 'left forearm': 6.5,
            'right hip': 6.8, 'left hip': 6.8, 'right knee': 6.5, 'left knee': 6.5,
            'right ankle': 6.0, 'left ankle': 6.0, 'right thigh': 6.5, 'left thigh': 6.5,
            'right shank': 5.5, 'left shank': 5.5, 'right foot': 5.0, 'left foot': 5.0
        }
        weights = pd.Series(manual_weights).reindex(df.columns).fillna(1.0)

        feature_contributions = df.apply(lambda row: row * weights, axis=1).mean()
        low_contribution_features = feature_contributions.nsmallest(3)

        feedback = []
        for feature in low_contribution_features.index:
            feedback.append(f"Improve {feature.replace('_', ' ')} for better results.")

        return overall_score, feedback
    except Exception as e:
        print(f"Error processing .mot file: {e}")
        raise

# Generate feedback using OpenAI GPT
# Updated function to generate GPT feedback with the new OpenAI Python API
def generate_gpt_feedback(overall_score, feedback):
    try:
        # Prepare input for GPT
        feedback_str = "\n".join(feedback)
        prompt = f"Based on the athlete's overall score of {overall_score:.2f}, generate feedback for improvement. Include the following suggestions:\n{feedback_str}\nProvide actionable and motivating feedback to the athlete."

        # Use the newer OpenAI API (v1.0.0 or higher)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or use another available model like "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are a coach helping athletes improve their performance."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        # Return the generated feedback
        gpt_feedback = response['choices'][0]['message']['content'].strip()
        return gpt_feedback
    except Exception as e:
        print(f"Error generating GPT feedback: {e}")
        return "Error generating feedback."


# Main Function
def evaluate_video(video_path):
    """
    Evaluate the uploaded video and return score and feedback.
    """
    try:
        # Step 1: Process the video
        output_dir = process_video_with_sports2d(video_path)

        # Step 2: Score the video
        overall_score, feedback = score_video_mot_file(output_dir, model_path)

        # Step 3: Generate GPT feedback
        gpt_feedback = generate_gpt_feedback(overall_score, feedback)

        # Step 4: Print results
        result_output = []
        result_output.append("\n===== Evaluation Results =====")
        result_output.append(f"Overall Score: {overall_score:.2f} / 5.0")
        result_output.append("Feedback:")
        for line in feedback:
            result_output.append(f"- {line}")
        result_output.append("\nGPT Feedback:")
        result_output.append(gpt_feedback)

        # Combine results into a single string
        final_result = "\n".join(result_output)
        print(final_result)

        return final_result
    except Exception as e:
        print(f"Error evaluating video: {e}")
        return f"Error evaluating video: {e}"

# Entry Point
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"Error: Video file does not exist at {video_path}")
        sys.exit(1)

    print(f"Evaluating video: {video_path}")
    evaluate_video(video_path)
