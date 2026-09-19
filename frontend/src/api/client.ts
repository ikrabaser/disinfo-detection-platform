/**
 * API client - HttpOnly cookie tabanli JWT auth akisi icin.
 *
 * ONEMLI: token'lar JS tarafindan hicbir zaman OKUNMAZ/saklanmaz; backend
 * login/refresh endpoint'leri access/refresh token'larini HttpOnly cookie
 * olarak set eder. Bu yuzden her istekte `credentials: "include"`
 * (axios icin `withCredentials: true`) kullanilmasi ZORUNLUDUR.
 */
import axios, { type AxiosInstance } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Basit bir 401 -> refresh -> retry interceptor iskeleti.
// TODO: gercek implementasyonda concurrent request'lerin ayni anda birden
// fazla refresh cagrisi yapmamasi icin bir "refreshing" kilidi eklenmelidir.
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        await apiClient.post("/auth/refresh/");
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh basarisiz - kullaniciyi login sayfasina yonlendirmek
        // cagiran koda birakilir (TODO: global auth store/context).
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: number;
  username: string;
  email: string;
  role: "admin" | "analyst" | "viewer";
  date_joined: string;
}

export async function login(username: string, password: string): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/login/", { username, password });
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout/");
}

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me/");
  return data;
}

export interface Analysis {
  id: number;
  claim_text: string;
  source_url: string | null;
  query: string;
  status: "pending" | "running" | "completed" | "failed";
  nlp_result: Record<string, unknown> | null;
  gnn_result: Record<string, unknown> | null;
  bot_analysis_result: Record<string, unknown> | null;
  source_verification_result: Record<string, unknown> | null;
  truth_score: number | null;
  created_at: string;
  updated_at: string;
}

export async function listAnalyses(): Promise<Analysis[]> {
  const { data } = await apiClient.get<{ results?: Analysis[] } | Analysis[]>("/analyses/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function getAnalysis(id: string | number): Promise<Analysis> {
  const { data } = await apiClient.get<Analysis>(`/analyses/${id}/`);
  return data;
}

export async function createAnalysis(payload: {
  claim_text: string;
  source_url?: string;
  query?: string;
}): Promise<Analysis> {
  const { data } = await apiClient.post<Analysis>("/analyses/", payload);
  return data;
}
