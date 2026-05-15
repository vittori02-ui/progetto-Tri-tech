import axios from "axios";

// Con Vite proxy (/auth, /skills, /users, ecc. vanno al backend)
// In produzione, cambia VITE_API_URL con l'URL del backend
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
