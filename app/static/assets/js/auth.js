const loginLabel = document.getElementById("login-button");
const signupLabel = document.getElementById("signup-button");

loginLabel.addEventListener("click", () => {
  document.title = "Braintext - Login";
});

signupLabel.addEventListener("click", () => {
  document.title = "Braintext - Sign up";
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
