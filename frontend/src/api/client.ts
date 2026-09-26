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
  is_active: boolean;
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

export interface AIClaim {
  id: string;
  text: string;
  check_worthy: boolean;
  rationale: string;
}

export interface AIEvidenceItem {
  id: string;
  title: string;
  url: string;
  source: string;
  published_at?: string | null;
  summary: string;
  content: string;
  content_status: string;
  evidence_type: string;
  claim_reviewed: string;
  rating: string;
  language: string;
  retrieval_source: string;
  metadata: Record<string, unknown>;
}

export interface AIClaimAssessment {
  claim_id: string;
  stance:
    | "support"
    | "contradict"
    | "neutral"
    | "insufficient";
  evidence_strength:
    | "low"
    | "medium"
    | "high";
  reasoning: string;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  neutral_evidence_ids: string[];
}

export interface AIManipulationSignal {
  signal_type: string;
  severity:
    | "low"
    | "medium"
    | "high";
  excerpt: string;
  explanation: string;
}

export interface AIAnalysisReport {
  provider: string;
  model: string;
  overall_evidence_status:
    | "supported"
    | "contradicted"
    | "mixed"
    | "insufficient";
  claims: AIClaim[];
  evidence: Record<
    string,
    AIEvidenceItem[]
  >;
  assessments: AIClaimAssessment[];
  manipulation_signals:
    AIManipulationSignal[];
  retrieval_mode: string;
  limitations: string[];
}

export interface AIAnalysisResult {
  status: string;
  provider?: string;
  model?: string;
  reason?: string;
  error_type?: string;
  report: AIAnalysisReport | null;
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
  ai_analysis_result: AIAnalysisResult | null;
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


export interface AnalysisModelRun {
  id: number;
  analysis: number;
  kind: "gnn" | "bot";
  source:
    | "pipeline"
    | "agent_tool"
    | "legacy_import";
  model_name: string;
  feature_set: string;
  graph_id_snapshot: number | null;
  result: Record<string, unknown>;
  cross_domain: boolean;
  generated_at: string;
}


export async function getAnalysisModelRuns(
  id: string | number
): Promise<AnalysisModelRun[]> {
  const { data } =
    await apiClient.get<AnalysisModelRun[]>(
      `/analyses/${id}/model-runs/`
    );

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


// ---------------------------------------------------------------------------
// VERITAS Assistant
// ---------------------------------------------------------------------------

export interface AgentProvider {
  name: string;
  model: string;
  configured: boolean;
  supports_tools: boolean;
}

export interface AssistantMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  provider: string;
  model: string;
  input_tokens: number | null;
  output_tokens: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface AssistantConversationSummary {
  id: string;
  title: string;
  provider: string;
  model: string;
  analysis: number | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface AssistantConversation {
  id: string;
  title: string;
  provider: string;
  model: string;
  analysis: number | null;
  messages: AssistantMessage[];
  created_at: string;
  updated_at: string;
}

export async function getAgentProviders(): Promise<
  AgentProvider[]
> {
  const { data } = await apiClient.get<{
    providers: AgentProvider[];
  }>("/agent/providers/");

  return data.providers;
}

export async function listAssistantConversations(): Promise<
  AssistantConversationSummary[]
> {
  const { data } = await apiClient.get<{
    conversations: AssistantConversationSummary[];
  }>("/agent/conversations/");

  return data.conversations;
}

export async function createAssistantConversation(
  payload: {
    title?: string;
    provider?: string;
    analysis_id?: number | null;
  }
): Promise<AssistantConversation> {
  const { data } =
    await apiClient.post<AssistantConversation>(
      "/agent/conversations/",
      payload
    );

  return data;
}

export async function getAssistantConversation(
  id: string
): Promise<AssistantConversation> {
  const { data } =
    await apiClient.get<AssistantConversation>(
      `/agent/conversations/${id}/`
    );

  return data;
}

export async function deleteAssistantConversation(
  id: string
): Promise<void> {
  await apiClient.delete(
    `/agent/conversations/${id}/`
  );
}

export async function sendAssistantMessage(
  conversationId: string,
  content: string
): Promise<{
  user_message: AssistantMessage;
  assistant_message: AssistantMessage;
}> {
  const { data } = await apiClient.post<{
    user_message: AssistantMessage;
    assistant_message: AssistantMessage;
  }>(
    `/agent/conversations/${conversationId}/messages/`,
    {
      content,
    }
  );

  return data;
}


export interface PasswordResetResponse {
  detail: string;
  cooldown_seconds?: number;
}


export interface PasswordResetVerifyResponse {
  detail: string;
  reset_token: string;
}


export async function requestPasswordReset(
  email: string
): Promise<PasswordResetResponse> {
  const { data } =
    await apiClient.post<PasswordResetResponse>(
      "/auth/password-reset/",
      {
        email,
      }
    );

  return data;
}


export async function verifyPasswordResetCode(
  email: string,
  code: string
): Promise<PasswordResetVerifyResponse> {
  const { data } =
    await apiClient.post<PasswordResetVerifyResponse>(
      "/auth/password-reset/verify/",
      {
        email,
        code,
      }
    );

  return data;
}


export async function confirmPasswordReset(
  payload: {
    reset_token: string;
    new_password: string;
    confirm_password: string;
  }
): Promise<PasswordResetResponse> {
  const { data } =
    await apiClient.post<PasswordResetResponse>(
      "/auth/password-reset/confirm/",
      payload
    );

  return data;
}


export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
}


export interface RegisterRequestResponse {
  detail: string;
  email: string;
  cooldown_seconds: number;
}


export interface RegisterVerifyResponse {
  id: number;
  username: string;
  email: string;
  role: "admin" | "analyst" | "viewer";
  date_joined: string;
}


export interface RegisterResendResponse {
  detail: string;
  cooldown_seconds?: number;
  retry_after?: number;
}


export async function registerUser(
  payload: RegisterPayload
): Promise<RegisterRequestResponse> {
  const { data } =
    await apiClient.post<RegisterRequestResponse>(
      "/auth/register/",
      payload
    );

  return data;
}


export async function verifyRegistrationCode(
  email: string,
  code: string
): Promise<RegisterVerifyResponse> {
  const { data } =
    await apiClient.post<RegisterVerifyResponse>(
      "/auth/register/verify/",
      {
        email,
        code,
      }
    );

  return data;
}


export async function resendRegistrationCode(
  email: string
): Promise<RegisterResendResponse> {
  const { data } =
    await apiClient.post<RegisterResendResponse>(
      "/auth/register/resend/",
      {
        email,
      }
    );

  return data;
}



export async function getUsers(): Promise<User[]> {
  const { data } =
    await apiClient.get<User[]>(
      "/auth/users/"
    );

  return data;
}


export async function updateUserRole(
  userId: number,
  role: User["role"]
): Promise<User> {
  const { data } =
    await apiClient.patch<User>(
      `/auth/users/${userId}/role/`,
      {
        role,
      }
    );

  return data;
}
