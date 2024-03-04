const txRef = document.getElementById("tx_ref");
const userID = document.getElementById("user_id");
const currentBal = document.getElementById("user-balance").innerText;
let rates;

const getRates = async () => {
  try {
    let response = await fetch("/rates");
    if (response.ok) {
      let data = await response.json();
      rates = data.rates;
    } else {
      console.log(response.status);
      console.log(await response.text());
      alert("Error getting rates, please refresh the page or contact support.");
    }
  } catch (error) {
    console.log(error);
    alert("Error getting rates, please refresh the page or contact support.");
  }
};
document.addEventListener("DOMContentLoaded", async () => {
  await getRates();
  calculateAmount();
});

const updateUserBal = () => {
  const currentBalEl = document.getElementById("user-balance");
  const btAmount = parseFloat(document.getElementById("bt_amount").value);
  const newAmount = parseFloat(currentBal.replace("BT", "").replace(/,/g, ""));
  currentBalEl.innerHTML = isNaN(btAmount)
    ? ` ${currentBal.replace("BT", "")}<span>BT</span>`
    : ` ${(btAmount + newAmount).toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}<span>BT</span>`;
};

const calculateBtAmount = () => {
  const amount = document.getElementById("amount");
  const btAmount = document.getElementById("bt_amount");
  const currency = document.getElementById("currency").value;
  if (!(currency === "USD")) {
    let newAmount = parseFloat(amount.value) / rates.USD;
    btAmount.value = (newAmount * 10).toFixed(2);
  } else {
    btAmount.value = amount.value * 10;
  }
  updateUserBal();
};

const calculateAmount = () => {
  const btAmount = document.getElementById("bt_amount");
  const amount = document.getElementById("amount");
  const currency = document.getElementById("currency").value;
  if (!(currency === "USD")) {
    const newAmount = parseFloat(btAmount.value) * rates.USD;
    amount.value = (newAmount / 10).toFixed(2);
  } else {
    amount.value = btAmount.value / 10;
  }
  updateUserBal();
};

document.getElementById("amount").addEventListener("input", calculateBtAmount);
document.getElementById("bt_amount").addEventListener("input", calculateAmount);
document.getElementById("currency").addEventListener("input", calculateAmount);

document.getElementById("submit-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  // get tx_ref
  const submitBtn = document.getElementById("flw-form-btn");
  submitBtn.classList.toggle("running");
  try {
    const payload = {
      user_id: userID.value,
      amount: document.getElementById("amount").value,
      currency: document.getElementById("currency").value,
    };
    let response = await fetch("/tx_ref", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (response.ok) {
      let data = await response.json();
      txRef.value = data.tx_ref;
      // submit form
      if (
        confirm(
          "You will be redirected to Flutterwave to complete your payment."
        )
      ) {
        e.target.submit();
        submitBtn.disabled = true;
      }
    } else {
      console.log(await response.text());
      console.log(response.status);
      alert(
        "Something went wrong, please refresh the page or contact support."
      );
    }
  } catch (error) {
    console.log(error);
    alert("Something went wrong, please refresh the page or contact support.");
  } finally {
    submitBtn.classList.toggle("running");
  }
});
