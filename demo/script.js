// Import Firebase modules
import { 
    initializeApp 
} from "https://www.gstatic.com/firebasejs/11.2.0/firebase-app.js";
import { 
    getAuth, 
    createUserWithEmailAndPassword, 
    signInWithEmailAndPassword, 
    onAuthStateChanged, 
    signOut 
} from "https://www.gstatic.com/firebasejs/11.2.0/firebase-auth.js";
import { 
    getDatabase, 
    ref, 
    set, 
    get, 
    child 
} from "https://www.gstatic.com/firebasejs/11.2.0/firebase-database.js";

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyC2--JwE8dsVBZNYOH4z5i3c4riaaHphtU",
    authDomain: "ai-evaluation-app.firebaseapp.com",
    databaseURL: "https://ai-evaluation-app-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "ai-evaluation-app",
    storageBucket: "ai-evaluation-app.appspot.com",
    messagingSenderId: "232811257209",
    appId: "1:232811257209:web:410c30237e83b88a2ba3a8",
    measurementId: "G-E0MY4SX6V3"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);

// DOM Elements
const loginSection = document.getElementById("login-section");
const signupSection = document.getElementById("signup-section");
const mainPage = document.getElementById("main-page");
const signupButton = document.getElementById("signup-button");
const backToLoginButton = document.getElementById("back-to-login");
const loginForm = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");
const userRoleSpan = document.getElementById("user-role");
const studentSection = document.getElementById("student-section");
const teacherSection = document.getElementById("teacher-section");
const logoutButton = document.getElementById("logout");
const viewResultsButton = document.getElementById("view-results");
const getScoreButton = document.getElementById("get-score");
const teacherGetScoreButton = document.getElementById("teacher-get-score");
const resultsDiv = document.getElementById("results");
const teacherResultsSection = document.getElementById("teacher-results-section");
const studentFileInput = document.getElementById("csv-upload");
const teacherFileInput = document.getElementById("csv-upload-teacher");

// Sport selectors
const studentSportSelect = document.getElementById("sport");
const teacherSportSelect = document.getElementById("sport-teacher");

// Available disciplines
const disciplines = [
    "Sprint Start",
    "Shot Put",
    "Long Jump",
    "Discus Throw"
];

// Populate sport disciplines dynamically
disciplines.forEach((discipline) => {
    const option = (value) => {
        const element = document.createElement("option");
        element.value = value.toLowerCase().replace(/\s+/g, "-");
        element.textContent = value;
        return element;
    };

    studentSportSelect.appendChild(option(discipline));
    teacherSportSelect.appendChild(option(discipline));
});

// State Management
let currentUser = null;

// Helper Function: Show/Hide Sections
const showSection = (section) => {
    [loginSection, signupSection, mainPage].forEach((sec) => (sec.style.display = "none"));
    section.style.display = "block";
};

// Helper Function: Reset Results and Inputs
const resetResultsAndInputs = () => {
    resultsDiv.innerHTML = "";
    teacherResultsSection.innerHTML = "";
    studentFileInput.value = "";
    teacherFileInput.value = "";
};

// Show Sign-Up Section
signupButton.addEventListener("click", () => showSection(signupSection));

// Back to Login
backToLoginButton.addEventListener("click", () => showSection(loginSection));

// Handle Sign-Up Form Submission
signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("new-username").value.trim();
    const password = document.getElementById("new-password").value.trim();
    const role = document.getElementById("role").value;

    if (!email || !password || !role) {
        alert("Please fill out all fields.");
        return;
    }

    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        await set(ref(database, `users/${user.uid}`), { email, role });

        alert("Sign-up successful! Please log in.");
        showSection(loginSection);
    } catch (error) {
        console.error("Error during sign-up:", error.message);
        alert(`Sign-up failed: ${error.message}`);
    }
});

// Handle Login Form Submission
loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        const snapshot = await get(child(ref(database), `users/${user.uid}`));
        if (snapshot.exists()) {
            const userData = snapshot.val();
            currentUser = { ...userData, uid: user.uid };

            userRoleSpan.textContent = userData.role;
            resetResultsAndInputs();
            showSection(mainPage);

            if (userData.role === "student") {
                studentSection.style.display = "block";
                teacherSection.style.display = "none";
            } else {
                teacherSection.style.display = "block";
                studentSection.style.display = "none";
            }
        } else {
            throw new Error("User data not found in the database.");
        }
    } catch (error) {
        console.error("Error during login:", error.message);
        alert(`Login failed: ${error.message}`);
    }
});

// Persist Authentication State
onAuthStateChanged(auth, async (user) => {
    if (user) {
        try {
            const snapshot = await get(child(ref(database), `users/${user.uid}`));
            if (snapshot.exists()) {
                const userData = snapshot.val();
                currentUser = { ...userData, uid: user.uid };

                if (userData.role === "teacher") {
                    console.log("User is a teacher. Proceeding to populate email dropdown.");
                    populateEmailDropdown();
                } else {
                    console.warn("User is not a teacher. Role:", userData.role);
                }
            } else {
                throw new Error("User data not found in the database.");
            }
        } catch (error) {
            console.error("Error fetching user data:", error.message);
        }
    } else {
        console.warn("No user is logged in.");
    }
});

// Handle "Get Score" for Students and Teachers
const handleGetScore = async (isTeacher = false) => {
    const sportSelector = isTeacher ? teacherSportSelect : studentSportSelect;
    const fileInput = isTeacher ? teacherFileInput : studentFileInput;
    const resultsContainer = isTeacher ? teacherResultsSection : resultsDiv;

    const selectedSport = sportSelector.value;
    const uploadedFile = fileInput.files[0];

    resultsContainer.innerHTML = ""; // Clear previous results

    if (!uploadedFile) {
        resultsContainer.innerHTML = "<p style='color: red;'>Please upload a video file.</p>";
        return;
    }

    const formData = new FormData();
    formData.append("video", uploadedFile);
    formData.append("discipline", selectedSport);

    const sanitizedFileName = uploadedFile.name.replace(/[.#$[\]]/g, "_");

    try {
        const response = await fetch("http://127.0.0.1:5000/upload", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Error: ${response.status}, ${errorText}`);
        }

        const data = await response.json();
        if (data.success) {
            resultsContainer.innerHTML = "<h3>Results:</h3>";
            data.results.forEach(({ person_id, score, feedback }) => {
                const resultDiv = document.createElement("div");
                resultDiv.innerHTML = `
                    <p><strong>${person_id}:</strong> ${score.toFixed(2)} / 5.0</p>
                    <ul>${feedback.map((item) => `<li>${item}</li>`).join("")}</ul>
                `;
                resultsContainer.appendChild(resultDiv);

                const userScoresRef = ref(
                    database,
                    `scores/${currentUser.uid}/${selectedSport}/${sanitizedFileName}`
                );

                set(userScoresRef, {
                    score: score,
                    feedback: feedback,
                })
                    .then(() => {
                        console.log("Score saved successfully to the database!");
                    })
                    .catch((error) => {
                        console.error("Error saving score to database:", error.message);
                    });
            });
        } else {
            resultsContainer.innerHTML = `<p style='color: red;'>${data.error}</p>`;
        }
    } catch (error) {
        console.error("Error fetching score:", error.message);
        resultsContainer.innerHTML = `<p style='color: red;'>An unexpected error occurred: ${error.message}</p>`;
    }
};

// Attach "Get Score" handlers
getScoreButton.addEventListener("click", () => handleGetScore(false));
teacherGetScoreButton.addEventListener("click", () => handleGetScore(true));

// Fetch and Display All Students' Results for Teachers
// Populate Email Dropdown with all user emails
const populateEmailDropdown = async () => {
    try {
        console.log("populateEmailDropdown called...");

        // Ensure the dropdown exists
        const emailSelect = document.getElementById("student-email-select");
        if (!emailSelect) {
            console.error("Dropdown element #student-email-select not found.");
            return;
        }

        // Fetch all users from Firebase
        const usersSnapshot = await get(ref(database, "users"));

        // Clear existing options
        emailSelect.innerHTML = '<option value="">-- Select an Email --</option>';

        if (usersSnapshot.exists()) {
            console.log("Users data fetched successfully.");
            const users = usersSnapshot.val();

            // Populate dropdown with user emails
            Object.keys(users).forEach((userId) => {
                const user = users[userId];
                if (user.email) {
                    const option = document.createElement("option");
                    option.value = userId;
                    option.textContent = user.email;
                    emailSelect.appendChild(option);
                }
            });

            if (emailSelect.options.length === 1) {
                emailSelect.innerHTML = '<option value="">No Emails Found</option>';
            }
        } else {
            console.warn("No users found in the database.");
        }
    } catch (error) {
        console.error("Error fetching users:", error.message);
    }
};

// Ensure this function is called after the DOM is fully loaded
document.addEventListener("DOMContentLoaded", () => {
    // Populate email dropdown only when the user is logged in as a teacher
    onAuthStateChanged(auth, (user) => {
        if (user) {
            populateEmailDropdown();
        }
    });
});


// Fetch and Display Results for Selected Email
const fetchResultsForEmail = async () => {
    const selectedUserId = document.getElementById("student-email-select").value;

    if (!selectedUserId) {
        alert("Please select an email.");
        return;
    }

    try {
        // Fetch scores for the selected user ID
        const scoresSnapshot = await get(ref(database, `scores/${selectedUserId}`));
        const teacherResultsSection = document.getElementById("teacher-results-section");

        if (!scoresSnapshot.exists()) {
            teacherResultsSection.innerHTML = `<p>No results found for the selected email.</p>`;
            return;
        }

        const scores = scoresSnapshot.val();
        let resultsHTML = `
            <h3>Results for Selected Email</h3>
            <table border="1" style="width: 100%; text-align: left;">
                <thead>
                    <tr>
                        <th>Discipline</th>
                        <th>Video Name</th>
                        <th>Score</th>
                        <th>Feedback</th>
                    </tr>
                </thead>
                <tbody>
        `;

        Object.keys(scores).forEach((discipline) => {
            Object.keys(scores[discipline]).forEach((videoName) => {
                const videoData = scores[discipline][videoName];
                const score = videoData?.score ?? "N/A"; // Default to "N/A" if undefined
                const feedback = Array.isArray(videoData?.feedback) ? videoData.feedback : []; // Ensure feedback is an array

                resultsHTML += `
                    <tr>
                        <td>${discipline}</td>
                        <td>${videoName}</td>
                        <td>${typeof score === "number" ? score.toFixed(2) : score}</td>
                        <td><ul>${feedback.map((f) => `<li>${f}</li>`).join("")}</ul></td>
                    </tr>
                `;
            });
        });

        resultsHTML += `</tbody></table>`;
        teacherResultsSection.innerHTML = resultsHTML;
    } catch (error) {
        console.error("Error fetching results:", error.message);
        document.getElementById("teacher-results-section").innerHTML = `<p style="color: red;">Error fetching results: ${error.message}</p>`;
    }
};

// Call populateEmailDropdown when teacher logs in


// Attach Event Listener for Fetch Results Button
document.getElementById("view-results").addEventListener("click", fetchResultsForEmail);

// Logout
logoutButton.addEventListener("click", async () => {
    try {
        await signOut(auth);
        currentUser = null;
        resetResultsAndInputs();
        showSection(loginSection);
    } catch (error) {
        console.error("Error during logout:", error.message);
        alert("Failed to log out.");
    }
});


