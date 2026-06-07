import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_admin, get_current_user
from app.database import get_db
from app.models import (
    ActivityRecord,
    ClusterAssignment,
    DataUpload,
    LifestyleFactor,
    Prediction,
    SleepRecord,
    User,
)
from app.schemas import (
    AdminStatsResponse,
    ClusterRequest,
    LifestyleAnalysisResponse,
    PredictionRequest,
    PredictionResponse,
    RecommendationResponse,
    SleepRecordResponse,
)
from app.services.analytics import LifestyleAnalyzer, PredictionEngine, RecommendationEngine
from app.services.clustering import ClusteringEngine
from app.services.preprocessing import DataPreprocessor

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _get_sleep_dataframe(db: Session, user_id: int) -> pd.DataFrame:
    records = db.query(SleepRecord).filter(SleepRecord.user_id == user_id).order_by(SleepRecord.date).all()
    if not records:
        return pd.DataFrame()
    data = [{
        "date": r.date,
        "total_sleep_minutes": r.total_sleep_minutes,
        "deep_sleep_minutes": r.deep_sleep_minutes,
        "light_sleep_minutes": r.light_sleep_minutes,
        "rem_sleep_minutes": r.rem_sleep_minutes,
        "awake_minutes": r.awake_minutes,
        "sleep_efficiency": r.sleep_efficiency,
        "sleep_score": r.sleep_score,
    } for r in records]
    df = pd.DataFrame(data)
    return DataPreprocessor.preprocess_sleep_data(df)


def _get_lifestyle_dataframe(db: Session, user_id: int) -> pd.DataFrame:
    records = db.query(LifestyleFactor).filter(LifestyleFactor.user_id == user_id).order_by(LifestyleFactor.date).all()
    if not records:
        return pd.DataFrame()
    return pd.DataFrame([{
        "date": r.date,
        "caffeine_mg": r.caffeine_mg,
        "alcohol_units": r.alcohol_units,
        "exercise_minutes": r.exercise_minutes,
        "screen_time_minutes": r.screen_time_minutes,
        "stress_level": r.stress_level,
        "mood_score": r.mood_score,
        "work_hours": r.work_hours,
    } for r in records])


@router.get("/sleep-records", response_model=list[SleepRecordResponse])
def get_sleep_records(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(SleepRecord).filter(SleepRecord.user_id == current_user.id).order_by(SleepRecord.date.desc()).limit(100).all()
    return records


@router.get("/summary")
def get_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    df = _get_sleep_dataframe(db, current_user.id)
    if df.empty:
        return {"message": "No sleep data available. Upload your wearable data to get started."}

    return {
        "total_records": len(df),
        "avg_sleep_hours": round(df["total_sleep_minutes"].mean() / 60, 2) if "total_sleep_minutes" in df.columns else 0,
        "avg_efficiency": round(df["sleep_efficiency"].mean(), 1) if "sleep_efficiency" in df.columns else 0,
        "avg_deep_minutes": round(df["deep_sleep_minutes"].mean(), 1) if "deep_sleep_minutes" in df.columns else 0,
        "avg_rem_minutes": round(df["rem_sleep_minutes"].mean(), 1) if "rem_sleep_minutes" in df.columns else 0,
        "date_range": {
            "start": df["date"].min().isoformat() if "date" in df.columns else None,
            "end": df["date"].max().isoformat() if "date" in df.columns else None,
        },
    }


@router.post("/cluster")
def run_clustering(
    request: ClusterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    df = _get_sleep_dataframe(db, current_user.id)
    if len(df) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 sleep records for clustering. Upload more data.")

    engine = ClusteringEngine(df)
    result = engine.cluster(algorithm=request.algorithm, n_clusters=request.n_clusters)

    assignment = ClusterAssignment(
        user_id=current_user.id,
        cluster_id=result["cluster_id"],
        cluster_label=result["cluster_label"],
        algorithm=result["algorithm"],
        silhouette_score=result["silhouette_score"],
        features=result.get("features"),
    )
    db.add(assignment)
    db.commit()

    return result


@router.get("/cluster/latest")
def get_latest_cluster(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assignment = (
        db.query(ClusterAssignment)
        .filter(ClusterAssignment.user_id == current_user.id)
        .order_by(ClusterAssignment.created_at.desc())
        .first()
    )
    if not assignment:
        return {"message": "No clustering results yet. Run clustering from the dashboard."}
    return {
        "cluster_id": assignment.cluster_id,
        "cluster_label": assignment.cluster_label,
        "algorithm": assignment.algorithm,
        "silhouette_score": assignment.silhouette_score,
        "created_at": assignment.created_at.isoformat(),
    }


@router.get("/lifestyle", response_model=LifestyleAnalysisResponse)
def lifestyle_analysis(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sleep_df = _get_sleep_dataframe(db, current_user.id)
    lifestyle_df = _get_lifestyle_dataframe(db, current_user.id)

    if not lifestyle_df.empty and not sleep_df.empty:
        sleep_df = sleep_df.copy()
        sleep_df["date"] = pd.to_datetime(sleep_df["date"]).dt.normalize()
        lifestyle_df["date"] = pd.to_datetime(lifestyle_df["date"]).dt.normalize()
        merged = pd.merge(sleep_df, lifestyle_df, on="date", how="inner")
        if "cluster" not in merged.columns:
            engine = ClusteringEngine(sleep_df)
            try:
                cluster_result = engine.cluster()
                sleep_df["cluster"] = cluster_result["labels"][:len(sleep_df)]
            except ValueError:
                pass

    analyzer = LifestyleAnalyzer(sleep_df, lifestyle_df)
    correlations = analyzer.correlation_analysis()

    return LifestyleAnalysisResponse(
        correlations=correlations,
        anova_results=analyzer.anova_testing(),
        chi_square_results=analyzer.chi_square_testing(),
        feature_importance=analyzer.feature_importance(),
    )


@router.post("/predict", response_model=PredictionResponse)
def predict_archetype(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    df = _get_sleep_dataframe(db, current_user.id)
    if df.empty:
        raise HTTPException(status_code=400, detail="No sleep data available for prediction.")

    try:
        engine = ClusteringEngine(df)
        cluster_result = engine.cluster()
        df["cluster"] = cluster_result["labels"]
    except ValueError:
        pass

    predictor = PredictionEngine(df)
    result = predictor.predict(model_type=request.model_type)

    prediction = Prediction(
        user_id=current_user.id,
        model_type=result["model_type"],
        predicted_archetype=result["predicted_archetype"],
        confidence=result["confidence"],
        feature_importance=result["feature_importance"],
        shap_values=result.get("shap_values"),
    )
    db.add(prediction)
    db.commit()

    return PredictionResponse(
        predicted_archetype=result["predicted_archetype"],
        confidence=result["confidence"],
        model_type=result["model_type"],
        feature_importance=result["feature_importance"],
        shap_plot=result.get("shap_plot", {}),
    )


@router.get("/recommendations", response_model=RecommendationResponse)
def get_recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sleep_df = _get_sleep_dataframe(db, current_user.id)
    lifestyle_df = _get_lifestyle_dataframe(db, current_user.id)

    assignment = (
        db.query(ClusterAssignment)
        .filter(ClusterAssignment.user_id == current_user.id)
        .order_by(ClusterAssignment.created_at.desc())
        .first()
    )
    archetype = assignment.cluster_label if assignment else "Balanced Restorer"

    engine = RecommendationEngine()
    return engine.generate(sleep_df, lifestyle_df, archetype)


@router.get("/admin/stats", response_model=AdminStatsResponse)
def admin_stats(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_sleep = db.query(SleepRecord).count()

    sleep_records = db.query(SleepRecord).all()
    avg_hours = 0.0
    avg_efficiency = 0.0
    if sleep_records:
        durations = [r.total_sleep_minutes for r in sleep_records if r.total_sleep_minutes]
        efficiencies = [r.sleep_efficiency for r in sleep_records if r.sleep_efficiency]
        avg_hours = sum(durations) / len(durations) / 60 if durations else 0
        avg_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 0

    assignments = db.query(ClusterAssignment).all()
    cluster_dist: dict[str, int] = {}
    for a in assignments:
        label = a.cluster_label or f"Cluster {a.cluster_id}"
        cluster_dist[label] = cluster_dist.get(label, 0) + 1

    uploads = db.query(DataUpload).all()
    completed = [u for u in uploads if u.status == "completed"]
    failed = [u for u in uploads if u.status == "failed"]
    quality_scores = [u.quality_score for u in completed if u.quality_score]

    recent = db.query(DataUpload).order_by(DataUpload.created_at.desc()).limit(10).all()

    return AdminStatsResponse(
        total_users=total_users,
        total_sleep_records=total_sleep,
        average_sleep_hours=round(avg_hours, 2),
        average_sleep_efficiency=round(avg_efficiency, 1),
        cluster_distribution=cluster_dist,
        data_quality_metrics={
            "total_uploads": len(uploads),
            "successful_uploads": len(completed),
            "failed_uploads": len(failed),
            "average_quality_score": round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0,
            "total_activity_records": db.query(ActivityRecord).count(),
        },
        recent_uploads=[{
            "id": u.id,
            "filename": u.filename,
            "source_type": u.source_type,
            "status": u.status,
            "records_imported": u.records_imported,
            "created_at": u.created_at.isoformat(),
        } for u in recent],
    )
