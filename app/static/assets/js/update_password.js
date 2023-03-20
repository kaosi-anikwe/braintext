const password = document.getElementById("password");
const specialCharErr = document.getElementById("special");
const tooShortErr = document.getElementById("too_short");
const number = document.getElementById("number");
const registerBtn = document.getElementById("submit-button");

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
  console.log("running");
  let pass = e.target.value;
  if (!pass.match(/[^A-Za-z0-9-' ']/i)) {
    specialCharErr.style.display = "block";
    specialCharErr.style.color = "red";
    specialChar = true;
  } else {
    specialCharErr.style.display = "none";
    specialChar = false;
  }
  if (pass.length < 8 || pass.length > 32) {
    tooShortErr.style.display = "block";
    tooShortErr.style.color = "red";
    tooShort = true;
  } else {
    tooShortErr.style.display = "none";
    tooShort = false;
  }
  if (!pass.match(/\d/)) {
    number.style.display = "block";
    number.style.color = "red";
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
