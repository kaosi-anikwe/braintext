const sendEmail = async (e) => {
  e.preventDefault();
  const loadingBtn = document.getElementById("contact-submit");
  loadingBtn.classList.toggle("running");

  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;
  const subject = document.getElementById("subject").value;
  const body = document.getElementById("contact-body").value;

  let payload = {
    name: name,
    email: email,
    subject: subject,
    body: body,
  };

  let response = await fetch("/send-email", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify(payload),
  });
  if (response.ok) {
    document.getElementById("sent-message").style.display = "block";
    document.getElementById("contact-form").reset();
    loadingBtn.classList.toggle("running");
  }
};

const form = document.getElementById("contact-form");

form.addEventListener("submit", sendEmail);
