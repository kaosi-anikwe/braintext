const loginLabel = document.getElementById("login-button");
const signupLabel = document.getElementById("signup-button");

loginLabel.addEventListener("click", () => {
  document.title = "Braintext - Login";
});

signupLabel.addEventListener("click", () => {
  document.title = "Braintext - Sign up";
});
