import os
import subprocess
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 
# Paths
UPLOAD_FOLDER = os.path.abspath("./backend/uploads")
MODELS = {
    "long-jump": os.path.abspath("./backend/long_jump_scoring_model_new.pkl"),
    "shot-put": os.path.abspath("./backend/shot_put_scoring_model_new.pkl"),
    "sprint-start": os.path.abspath("./backend/sprint_start_scoring_model_new.pkl"),
    "discus-throw": os.path.abspath("./backend/discus_throw_scoring_model_new.pkl"),
}
ALLOWED_EXTENSIONS = {"mp4"}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_video_with_sports2d(video_path):
    """
    Run the Sports2D command in the Conda 'sports2d' environment on Windows.
    """
    try:
        video_path = os.path.abspath(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        expected_output_dir = os.path.join(os.path.dirname(video_path), f"{video_name}_Sports2D")

        # Ensure the video file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Command for Windows to activate Conda and run Sports2D
        cmd = (
            f'cmd.exe /k "conda activate sports2d && sports2d '
            f'--save_vid false --save_img false --save_pose false '
            f'--show_graphs false --multiperson true --keypoint_likelihood_threshold 0.50 '
            f'--video_input {video_path} && exit"'
        )

        print(f"Running command: {cmd}")
        subprocess.run(cmd, shell=True, check=True)
        print("Sports2D processing completed successfully.")

        # Dynamically locate the output directory
        if os.path.exists(expected_output_dir):
            return expected_output_dir
        else:
            # Check the root directory in case the output is misplaced
            root_output_dir = os.path.join(os.getcwd(), f"{video_name}_Sports2D")
            if os.path.exists(root_output_dir):
                return root_output_dir
            else:
                raise FileNotFoundError(f"Output directory not found: {expected_output_dir}")

    except subprocess.CalledProcessError as cpe:
        print(f"Error running Sports2D: {cpe}")
        raise RuntimeError(f"Sports2D command failed: {cpe}")
    except Exception as e:
        print(f"Error processing video: {e}")
        raise


def load_person_mot_files(output_dir):
    """
    Locate and load .mot files for person00 in the output directory.
    """
    try:
        mot_files = [f for f in os.listdir(output_dir) if f.endswith(".mot")]
        print(f"Found .mot files: {mot_files}")

        filtered_files = [f for f in mot_files if "person00" in f]
        if not filtered_files:
            raise FileNotFoundError("No valid .mot files found for person00.")

        return [os.path.join(output_dir, f) for f in filtered_files]
    except Exception as e:
        print(f"Error locating .mot files: {e}")
        raise

def generate_feedback(discipline, low_contribution_features):
    """
    Generate discipline-specific feedback based on low-contribution features.
    """
    feedback_templates = {
        "long-jump": {
            "run_up": "Run-up should be accelerated without slowing down or tripping before the repulsion.",
            "repelling_foot": "Ensure the repelling foot is flat on the ground, with the center of gravity above it.",
            "knighthood": "Knighthood should be maintained until half of the jump for better posture.",
            "landing": "Landing should be performed with a sliding technique to ensure stability."
        },
        "shot-put": {
            "glide_phase": "Improve the glide phase by starting from a folded low leg with the back facing the throwing direction.",
            "accessory_leg": "The accessory leg should be pulled under the pelvis via a flat limp motion.",
            "release_angle": "The ball should be released at a 45° angle with the arm fully extended."
        },
        "sprint-start": {
            "pelvis_position": "Ensure the pelvis is slightly higher than the shoulders during the 'done' position.",
            "body_tension": "When pushing out, tense the body like a spear to align the head, back, and repulsive leg.",
            "toes_claw": "Actively claw at the ground with your toes during the sprint to maximize propulsion."
        },
        "discus-throw": {
            "intro_swing": "During the introductory swing, ensure the throwing arm is behind the full movement.",
            "jump_turn": "Use a jump turn with the ball of your foot to gain momentum.",
            "release": "Ensure the discus departs via the index finger for optimal release technique."
        }
    }

    feature_mappings = {
        "long-jump": {
            "right ankle": "landing", "left ankle": "landing",
            "right knee": "knighthood", "left knee": "knighthood",
            "right hip": "repelling_foot", "left hip": "repelling_foot",
            "right shoulder": "knighthood", "left shoulder": "knighthood",
            "trunk": "repelling_foot", "pelvis": "knighthood",
            "right foot": "run_up", "left foot": "run_up",
            "head": "landing", "right arm": "repelling_foot", "left arm": "repelling_foot",
            "right forearm": "knighthood", "left forearm": "knighthood",
            "right shank": "repelling_foot", "left shank": "repelling_foot",
            "right thigh": "knighthood", "left thigh": "knighthood"
        },
        "shot-put": {
            "right ankle": "glide_phase", "left ankle": "glide_phase",
            "right knee": "accessory_leg", "left knee": "accessory_leg",
            "right hip": "glide_phase", "left hip": "glide_phase",
            "right shoulder": "release_angle", "left shoulder": "release_angle",
            "right elbow": "release_angle", "left elbow": "release_angle",
            "right arm": "release_angle", "left arm": "release_angle",
            "right forearm": "release_angle", "left forearm": "release_angle",
            "trunk": "glide_phase", "pelvis": "glide_phase",
            "head": "release_angle", "right shank": "accessory_leg", "left shank": "accessory_leg",
            "right thigh": "glide_phase", "left thigh": "glide_phase"
        },
        "sprint-start": {
            "right ankle": "toes_claw", "left ankle": "toes_claw",
            "right knee": "body_tension", "left knee": "body_tension",
            "right hip": "pelvis_position", "left hip": "pelvis_position",
            "right shoulder": "body_tension", "left shoulder": "body_tension",
            "trunk": "body_tension", "pelvis": "pelvis_position",
            "right foot": "toes_claw", "left foot": "toes_claw",
            "head": "body_tension", "right arm": "body_tension", "left arm": "body_tension",
            "right forearm": "body_tension", "left forearm": "body_tension",
            "right shank": "toes_claw", "left shank": "toes_claw",
            "right thigh": "body_tension", "left thigh": "body_tension"
        },
        "discus-throw": {
            "right ankle": "jump_turn", "left ankle": "jump_turn",
            "right knee": "jump_turn", "left knee": "jump_turn",
            "right hip": "intro_swing", "left hip": "intro_swing",
            "right shoulder": "intro_swing", "left shoulder": "intro_swing",
            "trunk": "release", "pelvis": "intro_swing",
            "head": "release", "right foot": "jump_turn", "left foot": "jump_turn",
            "right arm": "release", "left arm": "release",
            "right forearm": "release", "left forearm": "release",
            "right shank": "release", "left shank": "release",
            "right thigh": "jump_turn", "left thigh": "jump_turn"
        }
    }
    
    # Retrieve the feedback template and feature mapping for the discipline
    discipline_feedback = feedback_templates.get(discipline, {})
    feature_mapping = feature_mappings.get(discipline, {})

    # Collect feedback based on low-contribution features
    feedback_set = set()
    for feature in low_contribution_features.index:
        feedback_key = feature_mapping.get(feature)
        if feedback_key and feedback_key in discipline_feedback:
            feedback_set.add(discipline_feedback[feedback_key])

    # Ensure at least 1 feedback, and at most 3
    feedback_list = list(feedback_set)
    if not feedback_list:
        feedback_list.append("Great job overall, but keep working on improving your technique.")
    return feedback_list[:3]  # Limit feedback to a maximum of 3

def score_person(mot_file_path, model_path, discipline):
    try:
        person_id = mot_file_path.split('_')[-1].replace('.mot', '')
        

        df = pd.read_csv(mot_file_path, sep="\t", engine="python", skiprows=10)

        df = df.drop(columns=['time'], errors='ignore')
        
        scaler = MinMaxScaler()
        df = df.transform(lambda x: (x - x.min()) / (x.max() - x.min()))
        
        model = joblib.load(model_path)
        print(f"Loaded model: {model_path}")
        
        model_feature_names = getattr(model, 'feature_names_in_', None)
        df = df.reindex(columns=model_feature_names, fill_value=0)
        
        
        predictions = model.predict(df)
        overall_score = predictions.mean()
        

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

        feedback = generate_feedback(discipline, low_contribution_features)

        return person_id, overall_score, feedback
    except Exception as e:
        print(f"Error processing .mot file: {e}")
        raise

@app.route("/")
def index():
    return "Flask server is running!"

@app.route("/upload", methods=["POST"])
def upload_video():
    """
    Handle video uploads, process them with Sports2D, and calculate scores.
    """
    if "video" not in request.files or "discipline" not in request.form:
        return jsonify({"error": "Missing video file or discipline.", "success": False}), 400

    file = request.files["video"]
    discipline = request.form["discipline"]
    
    print(f"Discipline received: {discipline}")

    if file and allowed_file(file.filename):
        filename = file.filename
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        try:
            output_dir = process_video_with_sports2d(save_path)
            mot_files = load_person_mot_files(output_dir)

            results = []
            model_path = MODELS.get(discipline)
            if not model_path:
                raise ValueError(f"Invalid discipline: {discipline}")

            for mot_file in mot_files:
                person_id, score, feedback = score_person(mot_file, model_path, discipline)
                results.append({"person_id": person_id, "score": score, "feedback": feedback})
            
            print(f"Results: {results}")  # Log results for debugging
            return jsonify({"results": results, "success": True}), 200
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            return jsonify({"error": f"Processing error: {str(e)}", "success": False}), 500

    return jsonify({"error": "Invalid file type.", "success": False}), 400



if __name__ == "__main__":
    app.run(debug=True)
