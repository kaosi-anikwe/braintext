const accountType = document.getElementById("account-type");
const txRef = document.getElementById("tx_ref");
const userID = document.getElementById("user_id");

const updateTx = () => {
  const txAmount = document.getElementById("tx_amount");
  let upgradeAccount = accountType.value;
  if (upgradeAccount === "stnrd") {
    txRef.value = `stnrd-${txID}`;
    txAmount.value = 750;
  } else if (upgradeAccount === "prmum") {
    txRef.value = `prmum-${txID}`;
    txAmount.value = 1000;
  }
};

accountType.addEventListener("change", updateTx);

window.addEventListener("load", updateTx);

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
