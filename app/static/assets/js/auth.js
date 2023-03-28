const loginLabel = document.getElementById("login-button");
const signupLabel = document.getElementById("signup-button");

loginLabel.addEventListener("click", () => {
  document.title = "BrainText - Login";
});

signupLabel.addEventListener("click", () => {
  document.title = "BrainText - Sign up";
});

const password = document.getElementById("password");
const specialCharErr = document.getElementById("special");
const tooShortErr = document.getElementById("too_short");
const number = document.getElementById("number");
const registerBtn = document.getElementById("sign-up-button");

addEventListener("load", () => {
  registerBtn.disabled = true;
});

let specialChar = true;
let tooShort = true;
let numberErr = true;

function checkError() {
  if (!specialChar && !tooShort && !numberErr) {
    // no errors
    registerBtn.disabled = false;
    registerBtn.style.cursor = "";
  } else if (specialChar || tooShort || numberErr) {
    // error(s)
    registerBtn.disabled = true;
    registerBtn.style.cursor = "default";
  }
}

const validate = (e) => {
  let pass = e.target.value;
  if (!pass.match(/[^A-Za-z0-9-' ']/i)) {
    specialCharErr.style.display = "block";
    specialCharErr.style.color = "#E0DEDE";
    specialChar = true;
  } else {
    specialCharErr.style.display = "none";
    specialChar = false;
  }
  if (pass.length < 8 || pass.length > 32) {
    tooShortErr.style.display = "block";
    tooShortErr.style.color = "#E0DEDE";
    tooShort = true;
  } else {
    tooShortErr.style.display = "none";
    tooShort = false;
  }
  if (!pass.match(/\d/)) {
    number.style.display = "block";
    number.style.color = "#E0DEDE";
    numberErr = true;
  } else {
    number.style.display = "none";
    numberErr = false;
  }
  checkError();
};

password.addEventListener("input", validate);

const confirmPassword = (e) => {
  let confirmPass = e.target.value;
  let password = document.getElementById("password");
  if (confirmPass !== password.value) {
    notMatch(e.target);
    notMatch(password);
  } else {
    match(e.target);
    match(password);
  }
};

const match = (el) => {
  el.style.border = "none";
  registerBtn.disabled = false;
  registerBtn.style.cursor = "";
};

const notMatch = (el) => {
  el.style.borderColor = "red";
  el.style.borderWidth = "1px";
  el.style.borderStyle = "solid";
  registerBtn.disabled = true;
  registerBtn.style.cursor = "default";
};

document
  .getElementById("confirm-password")
  .addEventListener("input", confirmPassword);

const forgotPassword = document.getElementById("forgot-password");
const authContainer = document.getElementById("auth-form");
const forgotPasswordContainer = document.getElementById("forgot-password-form");

forgotPassword.addEventListener("click", (e) => {
  e.preventDefault();
  let forgotBtn = document.getElementById("forgot-button");
  authContainer.remove();
  forgotPasswordContainer.hidden = false;
  forgotBtn.click();
});
