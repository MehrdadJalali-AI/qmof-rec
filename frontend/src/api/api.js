import axios from "axios";

/* =======================================
   AXIOS INSTANCE
======================================= */

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",

  timeout: 120000,
});

/* =======================================
   HEALTH CHECK
======================================= */

export async function healthCheck() {
  const response = await API.get("/");

  return response.data;
}

/* =======================================
   CHAT API
======================================= */

export async function askChat(question, topK = 5) {
  const response = await API.post("/chat/", {
    question: question,

    top_k: topK,
  });

  return response.data;
}

/* =======================================
   RECOMMENDATION API
   PHASE 1 / PHASE 2 / PHASE 3
======================================= */

export async function recommendMaterials(query, topK = 5) {
  const response = await API.post("/recommend/", {
    query: query,

    top_k: topK,
  });

  return response.data;
}

/* =======================================
   MATERIAL STRUCTURE API
   FOR 3D CIF VIEWER
======================================= */

export async function getMaterialStructure(qmofId) {
  const response = await API.get(`/materials/${qmofId}/structure`, {
    responseType: "text",
  });

  return response.data;
}

/* =======================================
   MATERIAL PREDICTION API
======================================= */

export async function predictMaterial(file) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await API.post("/materials/predict", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
}

/* =======================================
   EXPORT INSTANCE
======================================= */

export default API;
