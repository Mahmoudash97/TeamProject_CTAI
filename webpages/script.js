// JavaScript for handling user interactions

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
const teacherResults = document.getElementById("teacher-results");
const getScoreButton = document.getElementById("get-score");
const resultsDiv = document.getElementById("results");

// Simulated user data storage
let users = [];
let currentUser = null;

// Show sign-up section
signupButton.addEventListener("click", () => {
    loginSection.style.display = "none";
    signupSection.style.display = "block";
});

// Back to login
backToLoginButton.addEventListener("click", () => {
    signupSection.style.display = "none";
    loginSection.style.display = "block";
});

// Handle sign-up form submission
signupForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const newUsername = document.getElementById("new-username").value;
    const newPassword = document.getElementById("new-password").value;
    const role = document.getElementById("role").value;

    users.push({ username: newUsername, password: newPassword, role });
    alert("Sign-up successful! Please log in.");

    signupSection.style.display = "none";
    loginSection.style.display = "block";
});

// Handle login form submission
loginForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const user = users.find(
        (u) => u.username === username && u.password === password
    );

    if (user) {
        currentUser = user;
        loginSection.style.display = "none";
        mainPage.style.display = "block";
        userRoleSpan.textContent = user.role;

        if (user.role === "student") {
            studentSection.style.display = "block";
            teacherSection.style.display = "none";
        } else {
            teacherSection.style.display = "block";
            studentSection.style.display = "block"; // Teachers see the same section as students
        }
    } else {
        alert("Invalid username or password.");
    }
});

// Logout
logoutButton.addEventListener("click", () => {
    currentUser = null;
    mainPage.style.display = "none";
    loginSection.style.display = "block";
});

// Handle "Get Score" button for students
getScoreButton.addEventListener("click", () => {
    resultsDiv.textContent = "Your score is displayed here! (Simulated result)";
});

// Handle "View All Results" button for teachers
viewResultsButton.addEventListener("click", () => {
    if (currentUser.role === "teacher") {
        teacherResults.textContent = "All student results are displayed here! (Simulated data)";
    } else {
        alert("Error: Only teachers are allowed to view this section.");
    }
});

// Update sport disciplines for student and teacher sections
const studentSportSelect = document.getElementById("sport");
const teacherSportSelect = document.getElementById("sport-teacher");

const disciplines = [
    "Sprint Starts",
    "Shot Put",
    "High Jump",
    "Hurdles",
    "Long Jump",
    "Discus Throw",
    "Javelin",
    "Relay Receiver Performance"
];

disciplines.forEach((discipline) => {
    const studentOption = document.createElement("option");
    studentOption.value = discipline.toLowerCase().replace(/\s+/g, "-");
    studentOption.textContent = discipline;
    studentSportSelect.appendChild(studentOption);

    const teacherOption = document.createElement("option");
    teacherOption.value = discipline.toLowerCase().replace(/\s+/g, "-");
    teacherOption.textContent = discipline;
    teacherSportSelect.appendChild(teacherOption);
});
