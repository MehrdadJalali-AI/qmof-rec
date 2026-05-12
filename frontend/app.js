const API_URL = "http://127.0.0.1:8000/predict";

async function predictMaterial() {
  const fileInput = document.getElementById("cifFile");
  const loading = document.getElementById("loading");
  const resultCard = document.getElementById("resultCard");

  if (!fileInput.files.length) {
    alert("Please upload a CIF file.");
    return;
  }

  const file = fileInput.files[0];

  const formData = new FormData();
  formData.append("file", file);

  loading.classList.remove("hidden");
  resultCard.classList.add("hidden");

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Prediction failed.");
    }

    const data = await response.json();

    displayResult(data);
  } catch (error) {
    alert(error.message);
  } finally {
    loading.classList.add("hidden");
  }
}

function displayResult(data) {
  document.getElementById("resultCard").classList.remove("hidden");

  document.getElementById("materialType").innerText =
    data.predicted_material_type;

  document.getElementById("confidence").innerText =
    (data.confidence * 100).toFixed(2) + "%";

  document.getElementById("filename").innerText = data.filename;

  renderProbabilities(data.class_probabilities);
  renderGraphStats(data.graph_statistics);
}

function renderProbabilities(probabilities) {
  const container = document.getElementById("probabilities");
  container.innerHTML = "";

  for (const [label, prob] of Object.entries(probabilities)) {
    const percent = (prob * 100).toFixed(2);

    const row = document.createElement("div");
    row.className = "prob-row";

    row.innerHTML = `
      <div class="prob-label">
        <span>${label}</span>
        <span>${percent}%</span>
      </div>
      <div class="bar">
        <div class="bar-fill" style="width: ${percent}%"></div>
      </div>
    `;

    container.appendChild(row);
  }
}

function renderGraphStats(stats) {
  const tbody = document.getElementById("graphStats");
  tbody.innerHTML = "";

  for (const [key, value] of Object.entries(stats)) {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td><strong>${formatKey(key)}</strong></td>
      <td>${value}</td>
    `;

    tbody.appendChild(row);
  }
}

function formatKey(key) {
  return key.replaceAll("_", " ");
}
