from typing import Any, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

from app.services.preprocessing import DataPreprocessor, SLEEP_ARCHETYPES


class ClusteringEngine:
    FEATURES = DataPreprocessor.SLEEP_FEATURES

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.scaler = StandardScaler()
        self.features_df = self._prepare_features()
        self.scaled = self.scaler.fit_transform(self.features_df) if len(self.features_df) > 0 else np.array([])

    def _prepare_features(self) -> pd.DataFrame:
        available = [f for f in self.FEATURES if f in self.df.columns]
        if not available:
            available = self.df.select_dtypes(include=[np.number]).columns.tolist()
        return self.df[available].fillna(0)

    def find_optimal_k(self, max_k: int = 8) -> dict[str, Any]:
        if len(self.scaled) < 4:
            return {"optimal_k": 2, "inertias": [], "silhouette_scores": []}

        max_k = min(max_k, len(self.scaled) - 1)
        inertias = []
        sil_scores = []
        k_range = range(2, max_k + 1)

        for k in k_range:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(self.scaled)
            inertias.append(float(km.inertia_))
            sil_scores.append(float(silhouette_score(self.scaled, labels)))

        optimal_k = list(k_range)[int(np.argmax(sil_scores))]
        return {
            "optimal_k": optimal_k,
            "inertias": inertias,
            "silhouette_scores": sil_scores,
            "k_range": list(k_range),
        }

    def cluster(self, algorithm: str = "kmeans", n_clusters: Optional[int] = None) -> dict[str, Any]:
        if len(self.scaled) < 2:
            raise ValueError("Need at least 2 records for clustering")

        if n_clusters is None:
            n_clusters = self.find_optimal_k()["optimal_k"]

        n_clusters = min(n_clusters, len(self.scaled))

        if algorithm == "hierarchical":
            model = AgglomerativeClustering(n_clusters=n_clusters)
            labels = model.fit_predict(self.scaled)
        else:
            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = model.fit_predict(self.scaled)

        sil = float(silhouette_score(self.scaled, labels)) if n_clusters > 1 else 0.0

        cluster_stats = {}
        self.df = self.df.copy()
        self.df["cluster"] = labels

        for cid in range(n_clusters):
            cluster_data = self.df[self.df["cluster"] == cid]
            label = SLEEP_ARCHETYPES.get(cid % len(SLEEP_ARCHETYPES), f"Cluster {cid}")
            stats_dict = {}
            for feat in self.features_df.columns:
                if feat in cluster_data.columns:
                    stats_dict[feat] = {
                        "mean": float(cluster_data[feat].mean()),
                        "std": float(cluster_data[feat].std()),
                        "min": float(cluster_data[feat].min()),
                        "max": float(cluster_data[feat].max()),
                    }
            cluster_stats[str(cid)] = {"label": label, "count": int(len(cluster_data)), "features": stats_dict}

        optimal = self.find_optimal_k()
        user_label = int(labels[-1]) if len(labels) > 0 else 0
        archetype = SLEEP_ARCHETYPES.get(user_label % len(SLEEP_ARCHETYPES), f"Cluster {user_label}")

        return {
            "cluster_id": user_label,
            "cluster_label": archetype,
            "algorithm": algorithm,
            "silhouette_score": sil,
            "labels": labels.tolist(),
            "statistics": cluster_stats,
            "pca_plot": self._pca_plot(labels),
            "radar_chart": self._radar_chart(cluster_stats),
            "heatmap": self._heatmap(cluster_stats),
            "elbow_plot": self._elbow_plot(optimal),
            "silhouette_plot": self._silhouette_plot(labels, sil),
            "features": self.features_df.iloc[-1].to_dict() if len(self.features_df) > 0 else {},
        }

    def _pca_plot(self, labels: np.ndarray) -> dict:
        if len(self.scaled) < 2:
            return {}
        n_components = min(2, self.scaled.shape[1])
        pca = PCA(n_components=n_components)
        coords = pca.fit_transform(self.scaled)
        df_plot = pd.DataFrame({
            "PC1": coords[:, 0],
            "PC2": coords[:, 1] if n_components > 1 else [0] * len(coords),
            "cluster": labels.astype(str),
        })
        fig = px.scatter(df_plot, x="PC1", y="PC2", color="cluster", title="PCA Cluster Visualization",
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig.to_dict()

    def _radar_chart(self, cluster_stats: dict) -> dict:
        if not cluster_stats:
            return {}
        features = list(next(iter(cluster_stats.values()))["features"].keys())[:6]
        fig = go.Figure()
        for cid, data in cluster_stats.items():
            values = [data["features"].get(f, {}).get("mean", 0) for f in features]
            max_val = max(values) if values else 1
            normalized = [v / max_val if max_val else 0 for v in values]
            fig.add_trace(go.Scatterpolar(r=normalized + [normalized[0]], theta=features + [features[0]],
                                          fill="toself", name=data["label"]))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            title="Sleep Archetype Radar Chart",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig.to_dict()

    def _heatmap(self, cluster_stats: dict) -> dict:
        if not cluster_stats:
            return {}
        features = list(next(iter(cluster_stats.values()))["features"].keys())
        clusters = list(cluster_stats.keys())
        matrix = []
        for cid in clusters:
            row = [cluster_stats[cid]["features"].get(f, {}).get("mean", 0) for f in features]
            matrix.append(row)

        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=features,
            y=[cluster_stats[c]["label"] for c in clusters],
            colorscale="Viridis",
        ))
        fig.update_layout(title="Cluster Feature Heatmap", template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
        return fig.to_dict()

    def _elbow_plot(self, optimal: dict) -> dict:
        if not optimal.get("inertias"):
            return {}
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=optimal["k_range"], y=optimal["inertias"], mode="lines+markers", name="Inertia"))
        fig.update_layout(
            title="Elbow Method",
            xaxis_title="Number of Clusters (k)",
            yaxis_title="Inertia",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig.to_dict()

    def _silhouette_plot(self, labels: np.ndarray, avg_score: float) -> dict:
        if len(self.scaled) < 2:
            return {}
        sample_scores = silhouette_samples(self.scaled, labels)
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=sample_scores, nbinsx=20, name="Silhouette Scores"))
        fig.add_vline(x=avg_score, line_dash="dash", annotation_text=f"Avg: {avg_score:.3f}")
        fig.update_layout(title="Silhouette Score Distribution", template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
        return fig.to_dict()
