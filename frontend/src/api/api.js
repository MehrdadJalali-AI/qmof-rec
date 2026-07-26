import axios from "axios";

/* =======================================
   AXIOS INSTANCE
======================================= */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const API = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

/* =======================================
   AUTH TOKEN INTERCEPTORS
======================================= */

const TOKEN_KEY = "qmof_access_token";

API.interceptors.request.use((config) => {
  const token = window.localStorage?.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.localStorage?.removeItem(TOKEN_KEY);
      window.localStorage?.removeItem("qmof_refresh_token");
      window.localStorage?.removeItem("qmof_user");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

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

export async function askChat(question) {
  const response = await API.post("/chat/", {
    question: question,
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
   QUERY FEEDBACK API
======================================= */

export async function submitFeedback(query, qmofId, relevance, usefulness, comment = "") {
  const response = await API.post("/feedback/", {
    query,
    qmof_id: qmofId,
    relevance,
    usefulness,
    comment,
  });

  return response.data;
}

/* =======================================
   AUTH API
======================================= */

export async function registerUser(email, password, fullName) {
  const response = await API.post("/auth/register", {
    email,
    password,
    full_name: fullName,
  });
  return response.data;
}

export async function loginUser(email, password) {
  const response = await API.post("/auth/login", { email, password });
  return response.data;
}

export async function fetchCurrentUser() {
  const response = await API.get("/auth/me");
  return response.data;
}

export async function logoutUser(refreshToken) {
  await API.post("/auth/logout", { refresh_token: refreshToken });
}

export async function listFavorites() {
  const response = await API.get("/users/me/favorites");
  return response.data;
}

export async function addFavorite(qmofId, note = "") {
  const response = await API.post("/users/me/favorites", { qmof_id: qmofId, note });
  return response.data;
}

export async function removeFavorite(favoriteId) {
  await API.delete(`/users/me/favorites/${favoriteId}`);
}

/* =======================================
   EXPORT INSTANCE
======================================= */

export default API;
