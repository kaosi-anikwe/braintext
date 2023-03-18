var phoneNumber; // variable that will store number
var dialCode; // number country code
var pin; // variable to hold OTP

// Add number verfication
const phoneInputField = document.querySelector("#whatsapp-phone");
let phoneInput;
if (phoneInputField) {
  (() => {
    phoneInput = window.intlTelInput(phoneInputField, {
      preferredCountries: ["us", "gb", "ng"],
      utilsScript:
        "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js",
    });
  })();
}

const numberForm = document.getElementById("number-form");
numberForm.onsubmit = (e) => {
  e.preventDefault();
  const submitBtn = document.getElementById("verify-otp-submit-btn");
  submitBtn.classList.toggle("running");
  submitBtn.disabled = true;
  phoneNumber = phoneInput.getNumber();
  dialCode = phoneInput.s.dialCode;
  // Send OTP
  (async () => {
    let response = await fetch("/send-otp", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({ phone_no: phoneNumber }),
    });
    if (response.ok) {
      submitBtn.classList.toggle("running");
      submitBtn.disabled = false;
      let data = await response.json();
      if (data.error) {
        // show a different toast
        let toastItem = document.querySelector("#error-toast");
        toastItem.hidden = false;
        toastItem.classList.add("toast");
        toastItem.parentElement.classList.add("toast-container");
        let toast = new bootstrap.Toast(toastItem);
        toast.show();
      } else {
        console.log(data.otp);
        pin = parseInt(data.otp);
        // Show toast
        let toastItem = document.querySelector("#resent-toast");
        toastItem.hidden = false;
        toastItem.classList.add("toast");
        toastItem.parentElement.classList.add("toast-container");
        let toast = new bootstrap.Toast(toastItem);
        toast.show();
      }
    }
  })();

  // Hide digits of number
  let hiddenNumber = phoneNumber.replace("+", "");
  let newNumber = "+";
  for (let i = 0; i < hiddenNumber.length; i++) {
    if (i >= dialCode.length && i < phoneNumber.length - 3) {
      newNumber += "x";
    } else newNumber += hiddenNumber[i];
  }
  cardHeader.innerHTML = `Enter the 6-digit PIN sent to ${newNumber} on WhatsApp.`;
  numberRow.hidden = !numberRow.hidden;
  otpRow.hidden = !otpRow.hidden;
};

const $inp = $(".ap-otp-input");
$inp.on({
  paste(ev) {
    // Handle Pasting
    const clip = ev.originalEvent.clipboardData.getData("text").trim();
    // Allow numbers only
    if (!/\d{6}/.test(clip)) return ev.preventDefault(); // Invalid. Exit here
    // Split string to Array or characters
    const s = [...clip];
    // Populate inputs. Focus last input.
    $inp
      .val((i) => s[i])
      .eq(5)
      .focus();
  },
  input(ev) {
    // Handle typing
    const i = $inp.index(this);
    if (this.value) $inp.eq(i + 1).focus();
  },
  keydown(ev) {
    // Handle Deleting
    const i = $inp.index(this);
    if (!this.value && ev.key === "Backspace" && i) $inp.eq(i - 1).focus();
  },
});

const resendOTP = document.getElementById("resend-btn");
const cardHeader = document.getElementById("enter-code");
const numberRow = document.getElementById("add-number-row");
const otpRow = document.getElementById("verify-otp-row");
const sendOTP = document.getElementById("verify-number");
const changeNumber = document.getElementById("change-number");
const invalid = document.getElementById("invalid");
const expired = document.getElementById("expired");

// Resend OTP
if (resendOTP) {
  resendOTP.addEventListener("click", () => {
    resendOTP.parentElement.classList.toggle("running");
    resendOTP.style.cursor = "default";
    invalid.hidden = true;
    expired.hidden = true;
    const numbers = document.querySelectorAll(".ap-otp-input");
    numbers.forEach((item) => {
      item.value = "";
    });
    // Actually send OTP
    (async () => {
      let response = await fetch("/resend-otp", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ phone_no: phoneNumber }),
      });
      if (response.ok) {
        resendOTP.parentElement.classList.toggle("running");
        resendOTP.style.cursor = "pointer";
        let data = await response.json();
        console.log(data["otp"]);
        pin = parseInt(data["otp"]);
        // Show toast
        var toastItem = document.querySelector("#resent-toast");
        toastItem.classList.add("toast");
        toastItem.parentElement.classList.add("toast-container");
        var toast = new bootstrap.Toast(toastItem);
        toast.show();
      }
    })();
  });
}

// Cancel verification
changeNumber.addEventListener("click", () => {
  phoneInputField.value = "";
  numberRow.hidden = !numberRow.hidden;
  otpRow.hidden = !otpRow.hidden;
});

// Get & verify OTP submitted
const verifyForm = document.getElementById("verify-otp-form");
verifyForm.onsubmit = async (e) => {
  const submitBtn = document.getElementById("verify-otp-submit-btn");
  submitBtn.classList.toggle("running");
  submitBtn.disabled = true;
  e.preventDefault();
  const numbers = document.querySelectorAll(".ap-otp-input");
  let getOtp = "";
  numbers.forEach((item) => {
    getOtp += item.value;
  });
  const otp = parseInt(getOtp);
  invalid.hidden = otp === pin;
  if (otp === pin) {
    let response = await fetch("/verify-otp", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({ phone_no: phoneNumber }),
    });
    if (response.redirected) {
      window.location.href = response.url;
    } else {
      let data = await response.json();
      if (data.expired) {
        expired.hidden = false;
        submitBtn.classList.toggle("running");
        submitBtn.disabled = false;
      }
    }
  } else {
    submitBtn.classList.toggle("running");
    submitBtn.disabled = false;
  }
};
