// Edit Profile
const firstNameEl = document.getElementById("first_name");
const lastNameEl = document.getElementById("last_name");
const phoneNoEl = document.getElementById("phone_no");
const emailEl = document.getElementById("email");

const firstName = firstNameEl.value;
const lastName = lastNameEl.value;
const email = emailEl.value;
let phoneNo;
if (phoneNoEl) {
  phoneNo = phoneNoEl.value;
}

const checkMatch = () => {
  const editSubmitBtn = document.getElementById("edit-submit-btn");
  let firstNameEdit = false;
  let lastNameEdit = false;
  let phoneEdit = false;
  let emailEdit = false;
  if (firstNameEl.value === firstName) firstNameEdit = false;
  else firstNameEdit = true;
  if (phoneNoEl) {
    if (phoneNoEl.value === phoneNo) phoneEdit = false;
    else phoneEdit = true;
  }
  if (lastNameEl.value === lastName) lastNameEdit = false;
  else lastNameEdit = true;
  if (emailEl.value === email) emailEdit = false;
  else emailEdit = true;
  if (firstNameEdit || phoneEdit || lastNameEdit || emailEdit)
    editSubmitBtn.disabled = false;
  else editSubmitBtn.disabled = true;
};

window.addEventListener("input", checkMatch);
window.addEventListener("load", checkMatch);

// Edit account settings
const aiVoiceEl = document.getElementById("aiVoice");
const subExpiryEl = document.getElementById("subExpiry");
const changesMadeEl = document.getElementById("changesMade");
const newProductsEl = document.getElementById("newProducts");
const voiceResponseEl = document.getElementById("voice_response");

const subExpiry = subExpiryEl.checked;
const changesMade = changesMadeEl.checked;
const newProducts = newProductsEl.checked;
let aiVoice;
if (aiVoiceEl) aiVoice = aiVoiceEl.value;
let voiceResponse;
if (voiceResponseEl) voiceResponse = voiceResponseEl.checked;

const checkEdit = () => {
  const editProfileBtn = document.getElementById("edit-profile-btn");
  let subExpiryEdit = false;
  let changesMadeEdit = false;
  let newProductsEdit = false;
  let voiceResponseEdit = false;
  let aiVoiceEdit = false;
  if (subExpiryEl.checked === subExpiry) subExpiryEdit = false;
  else subExpiryEdit = true;
  if (aiVoiceEl) {
    if (aiVoiceEl.value === aiVoice) aiVoiceEdit = false;
    else aiVoiceEdit = true;
  }
  if (changesMadeEl.checked === changesMade) changesMadeEdit = false;
  else changesMadeEdit = true;
  if (newProductsEl.checked === newProducts) newProductsEdit = false;
  else newProductsEdit = true;
  if (voiceResponseEl) {
    if (voiceResponseEl.checked === voiceResponse) voiceResponseEdit = false;
    else voiceResponseEdit = true;
  }
  if (
    subExpiryEdit ||
    changesMadeEdit ||
    newProductsEdit ||
    aiVoiceEdit ||
    voiceResponseEdit
  )
    editProfileBtn.disabled = false;
  else editProfileBtn.disabled = true;
};

window.addEventListener("input", checkEdit);
window.addEventListener("load", checkEdit);

const sendVerificatonEmail = document.getElementById("send-verification-email");
sendVerificatonEmail.addEventListener("click", async () => {
  sendVerificatonEmail.classList.toggle("running");
  let response = await fetch("/send-verification-email");
  if (response.ok) {
    sendVerificatonEmail.classList.toggle("running");
    sendVerificatonEmail.innerText = "Email Sent";
    sendVerificatonEmail.disabled = true;
  }
});
