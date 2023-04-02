const accountType = document.getElementById("account-type");
const txRef = document.getElementById("tx_ref");
const userID = document.getElementById("user_id");
const makeRecurring = document.getElementById("make-recurring");

const updatePaymentPlan = () => {
  const paymentPlan = document.getElementById("payment_plan");
  if (makeRecurring.checked) {
    if (accountType.value == "stnrd") {
      paymentPlan.value = "94271"; // Update to real value
    } else if (accountType.value == "prmum") {
      paymentPlan.value = "94272"; // Upadte to real value
    }
  } else {
    paymentPlan.value = "";
  }
};

const updateTx = () => {
  const txAmount = document.getElementById("tx_amount");
  let submitBtn = document.getElementById("flw-form-btn");
  let stnrdPrice = document.getElementById("standard-pricing");
  let prmumPrice = document.getElementById("premium-pricing");
  let upgradeAccount = accountType.value;
  if (upgradeAccount === "stnrd") {
    txRef.value = `stnrd-${txID}`;
    txAmount.value = 1000;
    stnrdPrice.hidden = false;
    prmumPrice.hidden = true;
    submitBtn.disabled = false;
  } else if (upgradeAccount === "prmum") {
    txRef.value = `prmum-${txID}`;
    txAmount.value = 1200;
    submitBtn.disabled = false;
    stnrdPrice.hidden = true;
    prmumPrice.hidden = false;
  } else {
    stnrdPrice.hidden = true;
    prmumPrice.hidden = true;
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
