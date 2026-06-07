from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SleepRecordResponse(BaseModel):
    id: int
    date: datetime
    total_sleep_minutes: Optional[float]
    deep_sleep_minutes: Optional[float]
    light_sleep_minutes: Optional[float]
    rem_sleep_minutes: Optional[float]
    awake_minutes: Optional[float]
    sleep_efficiency: Optional[float]
    sleep_score: Optional[float]
    source: Optional[str]

    class Config:
        from_attributes = True


class ClusterRequest(BaseModel):
    algorithm: str = "kmeans"
    n_clusters: Optional[int] = None


class ClusterResponse(BaseModel):
    cluster_id: int
    cluster_label: str
    algorithm: str
    silhouette_score: Optional[float]
    statistics: dict[str, Any]
    pca_plot: dict[str, Any]
    radar_chart: dict[str, Any]
    heatmap: dict[str, Any]
    elbow_plot: Optional[dict[str, Any]] = None
    silhouette_plot: Optional[dict[str, Any]] = None


class LifestyleAnalysisResponse(BaseModel):
    correlations: dict[str, Any]
    anova_results: dict[str, Any]
    chi_square_results: dict[str, Any]
    feature_importance: list[dict[str, Any]]


class PredictionRequest(BaseModel):
    model_type: str = "random_forest"


class PredictionResponse(BaseModel):
    predicted_archetype: str
    confidence: float
    model_type: str
    feature_importance: list[dict[str, Any]]
    shap_plot: dict[str, Any]


class RecommendationResponse(BaseModel):
    suggestions: list[dict[str, str]]
    risk_alerts: list[dict[str, str]]
    lifestyle_tips: list[dict[str, str]]


class AdminStatsResponse(BaseModel):
    total_users: int
    total_sleep_records: int
    average_sleep_hours: float
    average_sleep_efficiency: float
    cluster_distribution: dict[str, int]
    data_quality_metrics: dict[str, Any]
    recent_uploads: list[dict[str, Any]]


class UploadResponse(BaseModel):
    id: int
    filename: str
    source_type: str
    records_imported: int
    quality_score: Optional[float]
    status: str
    message: str

    class Config:
        from_attributes = True
