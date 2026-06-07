from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class LifestyleAnalyzer:
    def __init__(self, sleep_df: pd.DataFrame, lifestyle_df: pd.DataFrame):
        self.sleep_df = sleep_df.copy()
        self.lifestyle_df = lifestyle_df.copy()
        self.merged = self._merge_data()

    def _merge_data(self) -> pd.DataFrame:
        if self.sleep_df.empty:
            return pd.DataFrame()
        sleep = self.sleep_df.copy()
        sleep["date"] = pd.to_datetime(sleep["date"]).dt.normalize()
        if self.lifestyle_df.empty:
            return sleep
        lifestyle = self.lifestyle_df.copy()
        lifestyle["date"] = pd.to_datetime(lifestyle["date"]).dt.normalize()
        return pd.merge(sleep, lifestyle, on="date", how="left", suffixes=("", "_life"))

    def correlation_analysis(self) -> dict[str, Any]:
        if self.merged.empty:
            return {"matrix": {}, "plot": {}}

        lifestyle_cols = [c for c in ["caffeine_mg", "alcohol_units", "exercise_minutes", "screen_time_minutes",
                                       "stress_level", "mood_score", "work_hours"] if c in self.merged.columns]
        sleep_cols = [c for c in ["total_sleep_minutes", "sleep_efficiency", "deep_sleep_minutes", "rem_sleep_minutes",
                                   "sleep_score"] if c in self.merged.columns]
        cols = lifestyle_cols + sleep_cols

        if len(cols) < 2:
            return {"matrix": {}, "plot": {}}

        corr = self.merged[cols].corr().round(4)
        fig = px.imshow(corr, text_auto=".2f", title="Lifestyle-Sleep Correlation Matrix",
                        color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")

        return {"matrix": corr.to_dict(), "plot": fig.to_dict()}

    def anova_testing(self) -> dict[str, Any]:
        results = {}
        if self.merged.empty or "cluster" not in self.merged.columns:
            return results

        test_features = [c for c in ["total_sleep_minutes", "sleep_efficiency", "caffeine_mg", "exercise_minutes"]
                         if c in self.merged.columns]

        for feat in test_features:
            groups = [group[feat].dropna().values for _, group in self.merged.groupby("cluster")]
            groups = [g for g in groups if len(g) > 0]
            if len(groups) >= 2:
                f_stat, p_value = stats.f_oneway(*groups)
                results[feat] = {
                    "f_statistic": float(f_stat),
                    "p_value": float(p_value),
                    "significant": p_value < 0.05,
                }
        return results

    def chi_square_testing(self) -> dict[str, Any]:
        results = {}
        if self.merged.empty:
            return results

        if "cluster" in self.merged.columns:
            for col in ["stress_level", "mood_score"]:
                if col not in self.merged.columns:
                    continue
                binned = pd.cut(self.merged[col].fillna(0), bins=3, labels=["low", "medium", "high"])
                contingency = pd.crosstab(self.merged["cluster"], binned)
                if contingency.shape[0] >= 2 and contingency.shape[1] >= 2:
                    chi2, p_value, dof, _ = stats.chi2_contingency(contingency)
                    results[col] = {
                        "chi2": float(chi2),
                        "p_value": float(p_value),
                        "dof": int(dof),
                        "significant": p_value < 0.05,
                    }
        return results

    def feature_importance(self) -> list[dict[str, Any]]:
        if self.merged.empty or "cluster" not in self.merged.columns:
            return []

        feature_cols = [c for c in self.merged.select_dtypes(include=[np.number]).columns
                        if c not in ["cluster", "id"]]
        if len(feature_cols) < 2:
            return []

        X = self.merged[feature_cols].fillna(0)
        y = self.merged["cluster"]

        if len(y.unique()) < 2:
            return []

        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X, y)
        importances = sorted(
            zip(feature_cols, rf.feature_importances_),
            key=lambda x: x[1],
            reverse=True,
        )
        return [{"feature": f, "importance": float(imp)} for f, imp in importances[:10]]


class PredictionEngine:
    ARCHETYPES = ["Early Bird Optimizer", "Night Owl Explorer", "Balanced Restorer", "Light Sleeper", "Deep Recovery Champion"]

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in ["cluster", "id"]]

    def predict(self, model_type: str = "random_forest") -> dict[str, Any]:
        if len(self.df) < 5 or len(self.feature_cols) < 2:
            return self._fallback_prediction(model_type)

        X = self.df[self.feature_cols].fillna(0)

        if "cluster" in self.df.columns and self.df["cluster"].nunique() >= 2:
            y = self.df["cluster"]
            le = LabelEncoder()
            y_encoded = le.fit_transform(y)

            X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

            if model_type == "xgboost":
                model = xgb.XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric="mlogloss")
            else:
                model = RandomForestClassifier(n_estimators=100, random_state=42)

            model.fit(X_train, y_train)
            proba = model.predict_proba(X.iloc[[-1]])[0]
            pred_idx = int(np.argmax(proba))
            confidence = float(proba[pred_idx])

            if hasattr(model, "feature_importances_"):
                importances = sorted(zip(self.feature_cols, model.feature_importances_), key=lambda x: x[1], reverse=True)
            else:
                importances = []

            archetype = self.ARCHETYPES[pred_idx % len(self.ARCHETYPES)]
            shap_plot = self._compute_shap(model, X.iloc[[-1]], model_type)
        else:
            return self._fallback_prediction(model_type)

        return {
            "predicted_archetype": archetype,
            "confidence": confidence,
            "model_type": model_type,
            "feature_importance": [{"feature": f, "importance": float(i)} for f, i in importances[:10]],
            "shap_plot": shap_plot,
            "shap_values": shap_plot.get("values", {}),
        }

    def _fallback_prediction(self, model_type: str) -> dict[str, Any]:
        latest = self.df.iloc[-1] if len(self.df) > 0 else {}
        total_sleep = latest.get("total_sleep_minutes", 420)
        deep_ratio = latest.get("deep_sleep_ratio", 0.2)

        if total_sleep < 360:
            archetype = "Light Sleeper"
        elif deep_ratio > 0.25:
            archetype = "Deep Recovery Champion"
        elif total_sleep > 480:
            archetype = "Night Owl Explorer"
        else:
            archetype = "Balanced Restorer"

        return {
            "predicted_archetype": archetype,
            "confidence": 0.65,
            "model_type": model_type,
            "feature_importance": [{"feature": "total_sleep_minutes", "importance": 0.35},
                                   {"feature": "deep_sleep_ratio", "importance": 0.25}],
            "shap_plot": {},
            "shap_values": {},
        }

    def _compute_shap(self, model, X_sample: pd.DataFrame, model_type: str) -> dict:
        if not SHAP_AVAILABLE or len(X_sample) == 0:
            return {}

        try:
            if model_type == "xgboost":
                explainer = shap.TreeExplainer(model)
            else:
                explainer = shap.TreeExplainer(model)

            shap_values = explainer.shap_values(X_sample)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]

            fig = shap.plots.bar(shap.Explanation(
                values=shap_values[0] if len(shap_values.shape) > 1 else shap_values,
                feature_names=list(X_sample.columns),
            ), show=False)

            import matplotlib.pyplot as plt
            plt.tight_layout()
            # Return structured data instead of matplotlib figure
            values = shap_values[0] if len(shap_values.shape) > 1 else shap_values
            feature_names = list(X_sample.columns)
            sorted_idx = np.argsort(np.abs(values))

            bar_fig = {
                "data": [{
                    "type": "bar",
                    "x": [float(values[i]) for i in sorted_idx],
                    "y": [feature_names[i] for i in sorted_idx],
                    "orientation": "h",
                    "marker": {"color": ["#6366f1" if values[i] > 0 else "#ef4444" for i in sorted_idx]},
                }],
                "layout": {
                    "title": "SHAP Feature Contributions",
                    "template": "plotly_dark",
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "xaxis": {"title": "SHAP Value"},
                },
            }
            plt.close("all")
            return {"plot": bar_fig, "values": dict(zip(feature_names, [float(v) for v in values]))}
        except Exception:
            return {}


class RecommendationEngine:
    def generate(self, sleep_df: pd.DataFrame, lifestyle_df: pd.DataFrame, archetype: str) -> dict[str, Any]:
        suggestions = []
        risk_alerts = []
        lifestyle_tips = []

        if sleep_df.empty:
            return {"suggestions": suggestions, "risk_alerts": risk_alerts, "lifestyle_tips": lifestyle_tips}

        latest = sleep_df.iloc[-1]
        avg_sleep = sleep_df["total_sleep_minutes"].mean() if "total_sleep_minutes" in sleep_df.columns else 420
        avg_efficiency = sleep_df["sleep_efficiency"].mean() if "sleep_efficiency" in sleep_df.columns else 85

        total_sleep = latest.get("total_sleep_minutes", avg_sleep)
        efficiency = latest.get("sleep_efficiency", avg_efficiency)
        deep = latest.get("deep_sleep_minutes", 0)
        rem = latest.get("rem_sleep_minutes", 0)

        if total_sleep < 420:
            suggestions.append({
                "category": "Duration",
                "title": "Increase Sleep Duration",
                "description": f"Your recent sleep ({total_sleep/60:.1f}h) is below the recommended 7 hours. Try going to bed 30 minutes earlier.",
                "priority": "high",
            })
            risk_alerts.append({
                "level": "warning",
                "title": "Insufficient Sleep",
                "description": "Chronic sleep deprivation increases risk of cardiovascular disease and cognitive impairment.",
            })

        if efficiency < 80:
            suggestions.append({
                "category": "Quality",
                "title": "Improve Sleep Efficiency",
                "description": "Your sleep efficiency is below optimal. Reduce time in bed without sleeping and maintain a consistent schedule.",
                "priority": "medium",
            })

        if deep < 60:
            suggestions.append({
                "category": "Deep Sleep",
                "title": "Boost Deep Sleep",
                "description": "Deep sleep supports physical recovery. Try avoiding alcohol and heavy meals before bedtime.",
                "priority": "medium",
            })

        if rem < 60:
            suggestions.append({
                "category": "REM Sleep",
                "title": "Enhance REM Sleep",
                "description": "REM sleep is crucial for memory consolidation. Maintain regular sleep times and limit caffeine after 2 PM.",
                "priority": "medium",
            })

        if not lifestyle_df.empty:
            latest_life = lifestyle_df.iloc[-1]
            caffeine = latest_life.get("caffeine_mg", 0)
            screen_time = latest_life.get("screen_time_minutes", 0)
            exercise = latest_life.get("exercise_minutes", 0)

            if caffeine > 200:
                lifestyle_tips.append({
                    "category": "Caffeine",
                    "title": "Reduce Caffeine Intake",
                    "description": f"You consumed {caffeine}mg caffeine recently. Limit to 200mg and avoid after 2 PM.",
                })

            if screen_time > 120:
                lifestyle_tips.append({
                    "category": "Screen Time",
                    "title": "Digital Sunset",
                    "description": "High screen time before bed disrupts melatonin. Use blue light filters and stop screens 1 hour before bed.",
                })

            if exercise < 30:
                lifestyle_tips.append({
                    "category": "Exercise",
                    "title": "Increase Physical Activity",
                    "description": "Regular exercise improves sleep quality. Aim for 30 minutes of moderate activity daily.",
                })
            elif exercise > 90:
                lifestyle_tips.append({
                    "category": "Exercise",
                    "title": "Timing Matters",
                    "description": "Intense exercise close to bedtime may disrupt sleep. Schedule workouts earlier in the day.",
                })

        archetype_tips = {
            "Early Bird Optimizer": "Maintain your early schedule but ensure you get enough wind-down time in the evening.",
            "Night Owl Explorer": "Gradually shift bedtime earlier by 15 minutes per week to align with natural circadian rhythms.",
            "Balanced Restorer": "Your sleep pattern is well-balanced. Focus on consistency during travel or schedule changes.",
            "Light Sleeper": "Create an optimal sleep environment: cool temperature (65-68°F), blackout curtains, and white noise.",
            "Deep Recovery Champion": "Your deep sleep is excellent. Maintain your current routine and recovery practices.",
        }

        if archetype in archetype_tips:
            suggestions.append({
                "category": "Archetype",
                "title": f"Tips for {archetype}",
                "description": archetype_tips[archetype],
                "priority": "low",
            })

        if total_sleep < 300:
            risk_alerts.append({
                "level": "critical",
                "title": "Severe Sleep Deprivation",
                "description": "Less than 5 hours of sleep significantly impairs immune function and increases accident risk.",
            })

        return {
            "suggestions": suggestions,
            "risk_alerts": risk_alerts,
            "lifestyle_tips": lifestyle_tips,
        }
