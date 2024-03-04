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

// FAQ -----------------------
document
  .getElementById("add-faq-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    e.target.classList.add("running");
    try {
      const payload = {
        action: "add",
        question: document.getElementById("new-faq-question").value,
        answer: document.getElementById("new-faq-answer").value,
      };
      let response = await fetch("/index-faq", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        flashMessage(
          "FAQ entered successfully. Refresh page to see changes.",
          "success"
        );
        window.location.reload();
      } else {
        console.log(await response.text());
        flashMessage(
          "There was an error. Refresh the page and try again.",
          "danger"
        );
      }
    } catch (error) {
      console.error(error);
      flashMessage(
        "Something went wrong. Please refresh the page and try again."
      );
    } finally {
      e.target.classList.remove("running");
    }
  });

document.querySelectorAll(".delete-faq").forEach((btn) => {
  btn.addEventListener("click", async (e) => {
    e.preventDefault();
    if (confirm("Delete FAQ?")) {
      try {
        const payload = {
          action: "delete",
          faq_id: btn.dataset.id,
        };
        let response = await fetch("/index-faq", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (response.ok) {
          flashMessage(
            "FAQ deleted successfully. Refresh page to see changes.",
            "success"
          );
          window.location.reload();
        } else {
          console.log(await response.text());
          flashMessage(
            "There was an error. Refresh the page and try again.",
            "danger"
          );
        }
      } catch (error) {
        console.error(error);
        flashMessage(
          "Something went wrong. Please refresh the page and try again."
        );
      }
    }
  });
});

document.querySelectorAll(".edit-faq").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    const answerDiv = document.getElementById(`faq-answer-${btn.dataset.id}`);
    const editForm = document.getElementById(`edit-form-${btn.dataset.id}`);
    answerDiv.hidden = true;
    editForm.hidden = false;
  });
});

document.querySelectorAll(".cancel-edit").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    const answerDiv = document.getElementById(`faq-answer-${btn.dataset.id}`);
    const editForm = document.getElementById(`edit-form-${btn.dataset.id}`);
    answerDiv.hidden = false;
    editForm.hidden = true;
  });
});

document.querySelectorAll(".edit-faq-form").forEach((form) => {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    e.target.classList.add("running");
    const id = form.dataset.id;
    try {
      const payload = {
        action: "edit",
        faq_id: id,
        question: document.getElementById(`edit-faq-question-${id}`).value,
        answer: document.getElementById(`edit-faq-answer-${id}`).value,
      };
      let response = await fetch("/index-faq", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        flashMessage(
          "FAQ entered successfully. Refresh page to see changes.",
          "success"
        );
        window.location.reload();
      } else {
        console.log(await response.text());
        flashMessage(
          "There was an error. Refresh the page and try again.",
          "danger"
        );
      }
    } catch (error) {
      console.error(error);
      flashMessage(
        "Something went wrong. Please refresh the page and try again."
      );
    } finally {
      e.target.classList.remove("running");
    }
  });
});
