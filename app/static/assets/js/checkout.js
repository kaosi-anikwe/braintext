const accountType = document.getElementById("account-type");
const txRef = document.getElementById("tx_ref");
const userID = document.getElementById("user_id");
const makeRecurring = document.getElementById("make-recurring");

const updatePaymentPlan = () => {
  const paymentPlan = document.getElementById("payment_plan");
  if (makeRecurring.checked) {
    if (accountType.value == "stnrd") {
      paymentPlan.value = "34260"; // Update to real value
    } else if (accountType.value == "prmum") {
      paymentPlan.value = "34261"; // Upadte to real value
    }
  } else {
    paymentPlan.value = "";
  }
};

const updateTx = () => {
  const txAmount = document.getElementById("tx_amount");
  let submitBtn = document.getElementById("flw-form-btn");
  let upgradeAccount = accountType.value;
  if (upgradeAccount === "stnrd") {
    txRef.value = `stnrd-${txID}`;
    txAmount.value = 750;
    submitBtn.disabled = false;
  } else if (upgradeAccount === "prmum") {
    txRef.value = `prmum-${txID}`;
    txAmount.value = 1000;
    submitBtn.disabled = false;
  } else {
    submitBtn.disabled = true;
  }
  updatePaymentPlan();
};
accountType.addEventListener("change", updateTx);

window.addEventListener("load", updateTx);

makeRecurring.addEventListener("change", updatePaymentPlan);

document.getElementById("submit-form").addEventListener("submit", async () => {
  let response = await fetch("/create-transaction", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      tx_ref: txRef.value,
    }),
  });
});
