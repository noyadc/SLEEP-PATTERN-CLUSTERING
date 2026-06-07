const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UploadRecord {
  id: number;
  filename: string;
  source_type: string;
  records_imported: number;
  quality_score: number;
  status: string;
  created_at: string;
}

export interface UploadResult {
  id: number;
  filename: string;
  source_type: string;
  records_imported: number;
  quality_score: number;
  status: string;
  message: string;
}

export interface Summary {
  total_records?: number;
  avg_sleep_hours?: number;
  avg_efficiency?: number;
  avg_deep_minutes?: number;
  avg_rem_minutes?: number;
  message?: string;
  date_range?: { start: string; end: string };
}

export interface ClusterInfo {
  cluster_id?: number;
  cluster_label?: string;
  algorithm?: string;
  silhouette_score?: number;
  created_at?: string;
  message?: string;
}

export interface ClusterResult {
  cluster_id: number;
  cluster_label: string;
  algorithm: string;
  silhouette_score: number;
  statistics: Record<string, { label: string; count: number; features: Record<string, { mean: number }> }>;
  pca_plot: Record<string, unknown>;
  radar_chart: Record<string, unknown>;
  heatmap: Record<string, unknown>;
  elbow_plot?: Record<string, unknown>;
  silhouette_plot?: Record<string, unknown>;
}

export interface LifestyleData {
  correlations: { matrix?: Record<string, unknown>; plot?: Record<string, unknown> };
  anova_results: Record<string, { f_statistic: number; p_value: number; significant: boolean }>;
  chi_square_results: Record<string, { chi2: number; p_value: number; significant: boolean }>;
  feature_importance: { feature: string; importance: number }[];
}

export interface PredictionResult {
  predicted_archetype: string;
  confidence: number;
  model_type: string;
  feature_importance: { feature: string; importance: number }[];
  shap_plot: { plot?: Record<string, unknown> };
}

export interface Recommendations {
  suggestions: { category: string; title: string; description: string; priority: string }[];
  risk_alerts: { level: string; title: string; description: string }[];
  lifestyle_tips: { category: string; title: string; description: string }[];
}

export interface AdminStats {
  total_users: number;
  total_sleep_records: number;
  average_sleep_hours: number;
  average_sleep_efficiency: number;
  cluster_distribution: Record<string, number>;
  data_quality_metrics: {
    total_uploads: number;
    successful_uploads: number;
    failed_uploads: number;
    average_quality_score: number;
    total_activity_records: number;
  };
  recent_uploads: {
    id: number;
    filename: string;
    source_type: string;
    status: string;
    records_imported: number;
    created_at: string;
  }[];
}

class ApiClient {
  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("token");
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json() as Promise<T>;
  }

  signup(email: string, password: string, fullName?: string): Promise<AuthResponse> {
    return this.request("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  login(email: string, password: string): Promise<AuthResponse> {
    return this.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  getMe(): Promise<User> {
    return this.request("/api/auth/me");
  }

  uploadFile(file: File, sourceType: string): Promise<UploadResult> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("source_type", sourceType);
    return this.request("/api/upload/", { method: "POST", body: formData });
  }

  getUploadHistory(): Promise<UploadRecord[]> {
    return this.request("/api/upload/history");
  }

  getSummary(): Promise<Summary> {
    return this.request("/api/analytics/summary");
  }

  runClustering(algorithm = "kmeans", nClusters?: number): Promise<ClusterResult> {
    return this.request("/api/analytics/cluster", {
      method: "POST",
      body: JSON.stringify({ algorithm, n_clusters: nClusters }),
    });
  }

  getLatestCluster(): Promise<ClusterInfo> {
    return this.request("/api/analytics/cluster/latest");
  }

  getLifestyleAnalysis(): Promise<LifestyleData> {
    return this.request("/api/analytics/lifestyle");
  }

  predict(modelType = "random_forest"): Promise<PredictionResult> {
    return this.request("/api/analytics/predict", {
      method: "POST",
      body: JSON.stringify({ model_type: modelType }),
    });
  }

  getRecommendations(): Promise<Recommendations> {
    return this.request("/api/analytics/recommendations");
  }

  getAdminStats(): Promise<AdminStats> {
    return this.request("/api/analytics/admin/stats");
  }
}

export const api = new ApiClient();
