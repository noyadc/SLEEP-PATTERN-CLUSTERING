import os
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import ActivityRecord, DataUpload, HealthMetric, SleepRecord, User
from app.schemas import UploadResponse
from app.services.preprocessing import DataPreprocessor, parse_upload

router = APIRouter(prefix="/api/upload", tags=["Data Upload"])


def _save_sleep_records(db: Session, user_id: int, df: pd.DataFrame, source: str) -> int:
    count = 0
    for _, row in df.iterrows():
        record = SleepRecord(
            user_id=user_id,
            date=row.get("date", datetime.utcnow()),
            total_sleep_minutes=row.get("total_sleep_minutes"),
            deep_sleep_minutes=row.get("deep_sleep_minutes"),
            light_sleep_minutes=row.get("light_sleep_minutes"),
            rem_sleep_minutes=row.get("rem_sleep_minutes"),
            awake_minutes=row.get("awake_minutes"),
            sleep_efficiency=row.get("sleep_efficiency"),
            sleep_score=row.get("sleep_score"),
            source=source,
        )
        db.add(record)
        count += 1
    return count


def _save_activity_records(db: Session, user_id: int, df: pd.DataFrame, source: str) -> int:
    count = 0
    activity_cols = ["steps", "calories_burned", "active_minutes", "distance_km", "heart_rate_avg"]
    if not any(c in df.columns for c in activity_cols):
        return 0

    for _, row in df.iterrows():
        record = ActivityRecord(
            user_id=user_id,
            date=row.get("date", datetime.utcnow()),
            steps=int(row["steps"]) if pd.notna(row.get("steps")) else None,
            calories_burned=row.get("calories_burned"),
            active_minutes=row.get("active_minutes"),
            distance_km=row.get("distance_km"),
            heart_rate_avg=row.get("heart_rate_avg"),
            source=source,
        )
        db.add(record)
        count += 1
    return count


@router.post("/", response_model=UploadResponse)
async def upload_data(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    valid_sources = ["fitbit", "garmin", "apple_health"]
    if source_type not in valid_sources:
        raise HTTPException(status_code=400, detail=f"Invalid source type. Must be one of: {valid_sources}")

    content = await file.read()
    upload_record = DataUpload(
        user_id=current_user.id,
        filename=file.filename or "unknown",
        source_type=source_type,
        status="processing",
    )
    db.add(upload_record)
    db.commit()

    try:
        raw_df = parse_upload(source_type, content)
        if raw_df.empty:
            raise ValueError("No sleep data found in uploaded file")

        processed_df = DataPreprocessor.preprocess_sleep_data(raw_df)
        quality_score = DataPreprocessor.compute_quality_score(processed_df)

        sleep_count = _save_sleep_records(db, current_user.id, processed_df, source_type)
        activity_count = _save_activity_records(db, current_user.id, processed_df, source_type)

        os.makedirs(settings.upload_dir, exist_ok=True)
        save_path = os.path.join(settings.upload_dir, f"{current_user.id}_{upload_record.id}_{file.filename}")
        with open(save_path, "wb") as f:
            f.write(content)

        upload_record.records_imported = sleep_count + activity_count
        upload_record.quality_score = quality_score
        upload_record.status = "completed"
        db.commit()
        db.refresh(upload_record)

        return UploadResponse(
            id=upload_record.id,
            filename=upload_record.filename,
            source_type=source_type,
            records_imported=upload_record.records_imported,
            quality_score=quality_score,
            status="completed",
            message=f"Successfully imported {sleep_count} sleep records and {activity_count} activity records.",
        )
    except Exception as e:
        upload_record.status = "failed"
        upload_record.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Upload processing failed: {str(e)}")


@router.get("/history")
def upload_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uploads = db.query(DataUpload).filter(DataUpload.user_id == current_user.id).order_by(DataUpload.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "filename": u.filename,
            "source_type": u.source_type,
            "records_imported": u.records_imported,
            "quality_score": u.quality_score,
            "status": u.status,
            "created_at": u.created_at.isoformat(),
        }
        for u in uploads
    ]
