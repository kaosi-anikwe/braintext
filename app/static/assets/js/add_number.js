// Add number verfication
const phoneInputField = document.querySelector("#whatsapp-phone");
let phoneInput;
if (phoneInputField) {
  window.onload = () => {
    phoneInput = window.intlTelInput(phoneInputField, {
      preferredCountries: ["us", "uk", "ng"],
      utilsScript:
        "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js",
    });
  };
}

const numberForm = document.getElementById("number-form");
numberForm.onsubmit = (e) => {
  e.preventDefault();
  console.log(phoneInput.getNumber());
};
