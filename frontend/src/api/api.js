import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",

  timeout: 120000,
});

/* -------------------- */
/* HEALTH CHECK */
/* -------------------- */

export async function healthCheck() {
  const res = await API.get("/");

  return res.data;
}

/* -------------------- */
/* CHAT */
/* -------------------- */

export async function askChat(
  question,

  topK = 5,
) {
  const res = await API.post(
    "/chat/",

    {
      question,

      top_k: topK,
    },
  );

  return res.data;
}

/* -------------------- */
/* RECOMMENDATION */
/* NEW PHASE-1 VERSION */
/* -------------------- */

export async function recommendMaterials(
  query,

  topK = 5,
) {
  const res = await API.post(
    "/recommend/",

    {
      query,

      top_k: topK,
    },
  );

  return res.data;
}

/* -------------------- */
/* MATERIAL PREDICTION */
/* -------------------- */

export async function predictMaterial(file) {
  const formData = new FormData();

  formData.append(
    "file",

    file,
  );

  const res = await API.post(
    "/materials/predict",

    formData,

    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return res.data;
}

export default API;
