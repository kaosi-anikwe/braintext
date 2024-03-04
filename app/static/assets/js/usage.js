const usgObj = {};
let monthChart;
let gpt3Chart;
let gpt4Chart;
let audioChart;
let imageChart;
let range;
const monthNames = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];
let currentMonthIndex = new Date().getMonth();
let currentYear = new Date().getFullYear();

const getUsage = async () => {
  try {
    document.getElementById("month-heading").classList.toggle("running");
    const month = currentMonthIndex + 1;
    const year = currentYear;
    if (usgObj.hasOwnProperty(`${currentMonthIndex}${currentYear}`)) {
      console.log(`Already fetched ${currentMonthIndex} ${currentYear}`);
      return;
    }
    console.log(`Fetching ${currentMonthIndex} ${currentYear}`);
    const payload = { month, year };
    let response = await fetch("/usage", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.getElementById("csrf_token").value,
      },
      body: JSON.stringify(payload),
    });
    if (response.ok) {
      let data = await response.json();
      usgObj[`${currentMonthIndex}${currentYear}`] = {};
      usgObj[`${currentMonthIndex}${currentYear}`].data = data.usage;
      usgObj[`${currentMonthIndex}${currentYear}`].total = data.total;
      range = data.range;
    } else {
      console.log(await response.text());
      alert(
        "An error occured while retrieving usage. Please refresh the page or contact support."
      );
    }
  } catch (error) {
    console.log(error);
    alert("Something went worng. Please refresh the page or contact support.");
  } finally {
    document.getElementById("month-heading").classList.toggle("running");
    document.getElementById("month-span").innerText = `${usgObj[
      `${currentMonthIndex}${currentYear}`
    ].total.toFixed(2)} BT`;
  }
};

const getHistory = async () => {
  try {
    document.getElementById("history-div").classList.toggle("running");
    const month = currentMonthIndex + 1;
    const year = currentYear;
    const payload = { month, year };
    let response = await fetch("/recharge-history", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.getElementById("csrf_token").value,
      },
      body: JSON.stringify(payload),
    });
    if (response.ok) {
      let data = await response.json();
      const historyList = document.getElementById("recharge-history");
      let innerHTML = "";
      for (const row of data.records) {
        const rowHTML = `<li class="list-group-item" style="background: inherit;">
                            <div class="row">
                                <div class="col-md-9">${row.date}</div>
                                <div class="col-md-3 text-secondary">${row.amount} BT</div>
                            </div>
                        </li>`;
        innerHTML += rowHTML;
      }
      historyList.innerHTML = innerHTML;
    } else {
      console.log(await response.text());
      alert(
        "An error occured while retrieving usage. Please refresh the page or contact support."
      );
    }
  } catch (error) {
    console.log(error);
    alert("Something went worng. Please refresh the page or contact support.");
  } finally {
    document.getElementById("history-div").classList.toggle("running");
  }
};

document.addEventListener("DOMContentLoaded", async () => {
  await getUsage();
  await getHistory();
  updateMonthDisplay(currentMonthIndex);
  const monthCtx = document.getElementById("monthly-spend");
  const gpt3Ctx = document.getElementById("gpt-3-chart");
  const gpt4Ctx = document.getElementById("gpt-4-chart");
  const audioCtx = document.getElementById("audio-chart");
  const imageCtx = document.getElementById("image-chart");
  monthChart = new Chart(monthCtx, {
    type: "bar",
    data: getMonthChartData(),
    options: {
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          padding: 10,
          titleColor: "#012970",
          bodyColor: "#012970",
          backgroundColor: "#F6F9FF",
          callbacks: {
            title: (ctx) => {
              let total = 0;
              ctx.forEach((ct) => (total += parseFloat(ct.formattedValue)));
              return `${ctx[0].label}    ${total.toFixed(2)} BT`;
            },
            label: (ctx) => {
              return `${ctx.dataset.label}    ${ctx.formattedValue} BT`;
            },
          },
        },
      },
      scales: {
        x: {
          stacked: true,
          grid: {
            display: false,
          },
          ticks: {
            maxRotation: 0,
            minRotation: 0,
            font: {
              size: 10,
            },
            callback: (value, index, ticks) => {
              const labels = usgObj[
                `${currentMonthIndex}${currentYear}`
              ].data.map((day) => Object.keys(day)[0]);
              if (index == 0 || index % 7 == 0) {
                return labels[index];
              }
              return "";
            },
          },
        },
        y: {
          stacked: true,
          ticks: {
            font: {
              size: 10,
            },
            callback: (value, index, ticks) => `${value} BT`,
          },
        },
      },
    },
  });

  gpt3Chart = new Chart(gpt3Ctx, {
    type: "bar",
    data: getOtherChartData("gpt_3", "GPT-3.5 Turbo"),
    options: otherChartOptions("GPT-3.5 Turbo"),
  });
  gpt4Chart = new Chart(gpt4Ctx, {
    type: "bar",
    data: getOtherChartData("gpt_4", "GPT-4 Turbo"),
    options: otherChartOptions("GPT-4 Turbo"),
  });
  audioChart = new Chart(audioCtx, {
    type: "bar",
    data: getOtherChartData("audio", "Audio models"),
    options: otherChartOptions("Audio models"),
  });
  imageChart = new Chart(imageCtx, {
    type: "bar",
    data: getOtherChartData("dalle", "Image models"),
    options: otherChartOptions("Image models"),
  });
});

const checkNext = () => {
  let checkMonth;
  let checkYear;
  if (currentMonthIndex < 11) {
    checkMonth = currentMonthIndex + 1;
    checkYear = currentYear;
  } else {
    checkMonth = 0;
    checkYear = currentYear + 1;
  }
  if (
    new Date(checkYear, checkMonth) > new Date(range[1].year, range[1].month)
  ) {
    document.getElementById("next-month").disabled = true;
    return false;
  } else {
    document.getElementById("next-month").disabled = false;
    return true;
  }
};

const checkPrev = () => {
  let checkMonth;
  let checkYear;
  if (currentMonthIndex > 0) {
    checkMonth = currentMonthIndex - 1;
    checkYear = currentYear;
  } else {
    checkMonth = 11;
    checkYear = currentYear - 1;
  }
  if (
    new Date(checkYear, checkMonth) < new Date(range[0].year, range[0].month)
  ) {
    document.getElementById("prev-month").disabled = true;
    return false;
  } else {
    document.getElementById("prev-month").disabled = false;
    return true;
  }
};

const updateMonthDisplay = (index) => {
  document.getElementById("month-display").value = monthNames[index];
  checkNext();
  checkPrev();
};

const getMonthChartData = () => {
  const data = {
    labels: usgObj[`${currentMonthIndex}${currentYear}`].data.map(
      (day) => Object.keys(day)[0]
    ),
    datasets: [
      {
        label: "GPT-3.5 Turbo",
        data: usgObj[`${currentMonthIndex}${currentYear}`].data.map(
          (day) => day[Object.keys(day)[0]].gpt_3
        ),
        backgroundColor: "#2487CE",
      },
      {
        label: "GPT-4 Turbo",
        data: usgObj[`${currentMonthIndex}${currentYear}`].data.map(
          (day) => day[Object.keys(day)[0]].gpt_4
        ),
        backgroundColor: "#75C7FF",
      },
      {
        label: "Image models",
        data: usgObj[`${currentMonthIndex}${currentYear}`].data.map(
          (day) => day[Object.keys(day)[0]].dalle
        ),
        backgroundColor: "#00C1FF",
      },
      {
        label: "Audio models",
        data: usgObj[`${currentMonthIndex}${currentYear}`].data.map(
          (day) => day[Object.keys(day)[0]].audio
        ),
        backgroundColor: "#4AA9FF",
      },
    ],
  };
  return data;
};

const getOtherChartData = (key, label) => {
  const data = {
    labels: usgObj[`${currentMonthIndex}${currentYear}`].data.map(
      (day) => Object.keys(day)[0]
    ),
    datasets: [
      {
        label: label,
        data: usgObj[`${currentMonthIndex}${currentYear}`].data.map(
          (day) => day[Object.keys(day)[0]][key]
        ),
        backgroundColor: "#2487CE",
      },
    ],
  };
  return data;
};

const otherChartOptions = (title) => {
  const options = {
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
    },
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        align: "start",
        padding: {
          bottom: 20,
        },
        font: {
          size: 14,
        },
        text: title,
      },
      tooltip: {
        padding: 10,
        titleColor: "#012970",
        bodyColor: "#012970",
        backgroundColor: "#F6F9FF",
        callbacks: {
          label: (ctx) => {
            return `${ctx.dataset.label}    ${ctx.formattedValue} BT`;
          },
        },
      },
    },
    scales: {
      x: {
        stacked: true,
        grid: {
          display: false,
        },
        ticks: {
          maxRotation: 0,
          minRotation: 0,
          font: {
            size: 10,
          },
          callback: (value, index, ticks) => {
            const labels = usgObj[
              `${currentMonthIndex}${currentYear}`
            ].data.map((day) => Object.keys(day)[0]);
            if (index == 0 || index % 6 == 0) {
              return labels[index];
            }
            return "";
          },
        },
      },
      y: {
        stacked: true,
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 10,
          },
          callback: (value, index, ticks) => `${value} BT`,
        },
      },
    },
  };
  return options;
};

document
  .getElementById("prev-month")
  .addEventListener("click", async function () {
    if (checkPrev()) {
      if (currentMonthIndex > 0) {
        currentMonthIndex -= 1;
      } else {
        currentMonthIndex = 11; // cycle back to December
        currentYear -= 1; // navigate to the previous year
      }
      updateMonthDisplay(currentMonthIndex);
    }
    checkNext();
    checkPrev();
    await getUsage();
    await getHistory();
    monthChart.data = getMonthChartData();
    monthChart.update();
    gpt3Chart.data = getOtherChartData("gpt_3", "GPT-3.5 Turbo");
    gpt4Chart.data = getOtherChartData("gpt_4", "GPT-4 Turbo");
    audioChart.data = getOtherChartData("audio", "Audio models");
    imageChart.data = getOtherChartData("dalle", "Image models");
    gpt3Chart.update();
    gpt4Chart.update();
    audioChart.update();
    imageChart.update();
  });

document
  .getElementById("next-month")
  .addEventListener("click", async function () {
    if (checkNext()) {
      if (currentMonthIndex < 11) {
        currentMonthIndex += 1;
      } else {
        currentMonthIndex = 0; // cycle back to January
        currentYear += 1; // navigate to the next year
      }

      updateMonthDisplay(currentMonthIndex);
    }
    checkNext();
    checkPrev();
    await getUsage();
    await getHistory();
    monthChart.data = getMonthChartData();
    monthChart.update();
    gpt3Chart.data = getOtherChartData("gpt_3", "GPT-3.5 Turbo");
    gpt4Chart.data = getOtherChartData("gpt_4", "GPT-4 Turbo");
    audioChart.data = getOtherChartData("audio", "Audio models");
    imageChart.data = getOtherChartData("dalle", "Image models");
    gpt3Chart.update();
    gpt4Chart.update();
    audioChart.update();
    imageChart.update();
  });
