import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

// Attach the access token to every outgoing request.
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, try a silent refresh once before giving up.
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  page_count: number | null;
  summary: string | null;
  created_at: string;
}

export interface SourceCitation {
  document_id: string;
  filename: string;
  chunk_index: number;
  excerpt: string;
  score: number;
}

export const auth = {
  login: (email: string, password: string) =>
    api.post("/api/v1/auth/login", { email, password }),
  register: (email: string, password: string, full_name?: string) =>
    api.post("/api/v1/auth/register", { email, password, full_name }),
  me: () => api.get("/api/v1/auth/me"),
};

export const documents = {
  list: () => api.get<Document[]>("/api/v1/documents"),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<Document>("/api/v1/documents/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  remove: (id: string) => api.delete(`/api/v1/documents/${id}`),
};

export const rag = {
  query: (question: string, document_ids?: string[]) =>
    api.post("/api/v1/query", { question, document_ids }),
  summarize: (document_id: string) => api.post("/api/v1/summarize", { document_id }),
  compare: (document_id_a: string, document_id_b: string, focus?: string) =>
    api.post("/api/v1/compare", { document_id_a, document_id_b, focus }),
  report: (document_ids: string[], title: string, instructions?: string) =>
    api.post("/api/v1/report", { document_ids, title, instructions }),
};

export const admin = {
  stats: () => api.get("/api/v1/admin/stats"),
  users: () => api.get("/api/v1/admin/users"),
};
