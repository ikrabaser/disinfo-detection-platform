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
    const requestUrl = originalRequest?.url ?? "";

    const isRefreshRequest =
      requestUrl.includes("/auth/refresh/");

    const isLoginRequest =
      requestUrl.includes("/auth/login/");

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isRefreshRequest &&
      !isLoginRequest
    ) {
      originalRequest._retry = true;

      try {
        await apiClient.post("/auth/refresh/");
        return apiClient(originalRequest);
      } catch (refreshError) {
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
  propagation_graph: number | null;
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

export interface RunAnalysisResponse {
  detail: string;
  analysis_id: number;
  job_id: number;
  status: string;
}

export async function runAnalysis(
  id: string | number
): Promise<RunAnalysisResponse> {
  const { data } =
    await apiClient.post<RunAnalysisResponse>(
      `/analyses/${id}/run/`
    );

  return data;
}


export interface NLPSummary {
  engine: string;
  total: number;
  labels: {
    gercek: number;
    belirsiz: number;
    sahte: number;
  };
  suspicious_count: number;
  suspicious_ratio: number;
  average_confidence: number;
}

export type LatestPropagationGraphResponse =
  import("../types").PropagationGraphData & {
    id: number;
    query: string;
    node_count: number;
    edge_count: number;
    nlp_summary: NLPSummary;
    created_at: string;
  };

export async function getPropagationGraph(
  id: string | number
): Promise<LatestPropagationGraphResponse> {
  const { data } =
    await apiClient.get<LatestPropagationGraphResponse>(
      `/social/graphs/${id}/`
    );

  return data;
}


export async function getLatestPropagationGraph(): Promise<LatestPropagationGraphResponse> {
  const { data } =
    await apiClient.get<LatestPropagationGraphResponse>(
      "/social/graphs/latest/"
    );

  return data;
}


export interface SocialIngestResponse {
  source: string;
  query: string;
  post_count: number;
  graph_id: number;
  node_count: number;
  edge_count: number;
  nlp_summary: NLPSummary;
  posts: Array<Record<string, unknown>>;
  graph: import("../types").PropagationGraphData;
}

export async function ingestSocialQuery(
  query: string,
  maxResults = 10
): Promise<SocialIngestResponse> {
  const { data } = await apiClient.post<SocialIngestResponse>(
    "/social/ingest/",
    {
      query,
      max_results: maxResults,
    }
  );

  return data;
}
