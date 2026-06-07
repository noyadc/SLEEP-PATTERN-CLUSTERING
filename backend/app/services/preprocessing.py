import io
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats


SLEEP_ARCHETYPES = {
    0: "Early Bird Optimizer",
    1: "Night Owl Explorer",
    2: "Balanced Restorer",
    3: "Light Sleeper",
    4: "Deep Recovery Champion",
}


class DataPreprocessor:
    """Handle missing values, outliers, time normalization, and feature engineering."""

    SLEEP_FEATURES = [
        "total_sleep_minutes",
        "deep_sleep_minutes",
        "light_sleep_minutes",
        "rem_sleep_minutes",
        "awake_minutes",
        "sleep_efficiency",
        "sleep_score",
        "deep_sleep_ratio",
        "rem_sleep_ratio",
        "sleep_latency_proxy",
    ]

    @staticmethod
    def detect_outliers(df: pd.DataFrame, columns: list[str], z_threshold: float = 3.0) -> pd.DataFrame:
        cleaned = df.copy()
        for col in columns:
            if col not in cleaned.columns:
                continue
            series = cleaned[col].dropna()
            if len(series) < 5:
                continue
            z_scores = np.abs(stats.zscore(series))
            outlier_idx = series.index[z_scores > z_threshold]
            cleaned.loc[outlier_idx, col] = np.nan
        return cleaned

    @staticmethod
    def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        cleaned = df.copy()
        numeric_cols = cleaned.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if cleaned[col].notna().sum() > 0:
                cleaned[col] = cleaned[col].fillna(cleaned[col].median())
            else:
                cleaned[col] = cleaned[col].fillna(0)
        return cleaned

    @staticmethod
    def normalize_time_columns(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
        cleaned = df.copy()
        if date_col in cleaned.columns:
            cleaned[date_col] = pd.to_datetime(cleaned[date_col], errors="coerce")
            cleaned = cleaned.dropna(subset=[date_col])
            cleaned = cleaned.sort_values(date_col)
        return cleaned

    @staticmethod
    def engineer_sleep_features(df: pd.DataFrame) -> pd.DataFrame:
        engineered = df.copy()
        total = engineered.get("total_sleep_minutes", pd.Series([0] * len(engineered)))
        total = total.replace(0, np.nan)

        if "deep_sleep_minutes" in engineered.columns:
            engineered["deep_sleep_ratio"] = engineered["deep_sleep_minutes"] / total
        if "rem_sleep_minutes" in engineered.columns:
            engineered["rem_sleep_ratio"] = engineered["rem_sleep_minutes"] / total
        if "awake_minutes" in engineered.columns:
            engineered["sleep_latency_proxy"] = engineered["awake_minutes"] / (total + engineered["awake_minutes"].fillna(0))

        if "sleep_efficiency" not in engineered.columns and "total_sleep_minutes" in engineered.columns:
            bed_time = engineered.get("awake_minutes", 0) + engineered.get("total_sleep_minutes", 0)
            engineered["sleep_efficiency"] = (engineered["total_sleep_minutes"] / bed_time.replace(0, np.nan)) * 100

        engineered = engineered.fillna(0)
        return engineered

    @classmethod
    def preprocess_sleep_data(cls, df: pd.DataFrame) -> pd.DataFrame:
        df = cls.normalize_time_columns(df)
        numeric_cols = [c for c in df.columns if c != "date" and pd.api.types.is_numeric_dtype(df[c])]
        df = cls.detect_outliers(df, numeric_cols)
        df = cls.handle_missing_values(df)
        df = cls.engineer_sleep_features(df)
        return df

    @staticmethod
    def compute_quality_score(df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        completeness = df.notna().mean().mean()
        row_count_score = min(len(df) / 30, 1.0)
        return round(float(completeness * 0.7 + row_count_score * 0.3) * 100, 2)


class FitbitParser:
    @staticmethod
    def parse(content: bytes) -> pd.DataFrame:
        df = pd.read_csv(io.BytesIO(content))
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        column_map = {
            "minutesasleep": "total_sleep_minutes",
            "minutesawake": "awake_minutes",
            "minutesindbed": "in_bed_minutes",
            "minutesofdeep": "deep_sleep_minutes",
            "minutesoflight": "light_sleep_minutes",
            "minutesofrem": "rem_sleep_minutes",
            "sleep_efficiency": "sleep_efficiency",
            "starttime": "date",
            "dateofsleep": "date",
            "logid": "log_id",
        }

        for old, new in column_map.items():
            if old in df.columns:
                df = df.rename(columns={old: new})

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        if "total_sleep_minutes" not in df.columns and "in_bed_minutes" in df.columns:
            awake = df.get("awake_minutes", 0)
            df["total_sleep_minutes"] = df["in_bed_minutes"] - awake

        df["source"] = "fitbit"
        return df


class GarminParser:
    @staticmethod
    def parse(content: bytes) -> pd.DataFrame:
        df = pd.read_csv(io.BytesIO(content))
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        column_map = {
            "sleep_time": "total_sleep_minutes",
            "deep_sleep": "deep_sleep_minutes",
            "light_sleep": "light_sleep_minutes",
            "rem_sleep": "rem_sleep_minutes",
            "awake_time": "awake_minutes",
            "sleep_date": "date",
            "calendar_date": "date",
            "score": "sleep_score",
            "steps": "steps",
            "calories": "calories_burned",
        }

        for old, new in column_map.items():
            if old in df.columns:
                df = df.rename(columns={old: new})

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Garmin often reports in seconds
        for col in ["total_sleep_minutes", "deep_sleep_minutes", "light_sleep_minutes", "rem_sleep_minutes", "awake_minutes"]:
            if col in df.columns and df[col].max() > 600:
                df[col] = df[col] / 60

        df["source"] = "garmin"
        return df


class AppleHealthParser:
    @staticmethod
    def parse(content: bytes) -> pd.DataFrame:
        root = ET.fromstring(content)
        records = []

        sleep_types = {
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryTypeIdentifierSleepAnalysisInBed",
            "HKCategoryTypeIdentifierSleepAnalysisAsleep",
            "HKCategoryTypeIdentifierSleepAnalysisAwake",
            "HKCategoryTypeIdentifierSleepAnalysisDeep",
            "HKCategoryTypeIdentifierSleepAnalysisREM",
            "HKCategoryTypeIdentifierSleepAnalysisCore",
        }

        for record in root.iter("Record"):
            record_type = record.get("type", "")
            if not any(st in record_type for st in sleep_types):
                continue

            start = record.get("startDate")
            end = record.get("endDate")
            if not start or not end:
                continue

            start_dt = pd.to_datetime(start)
            end_dt = pd.to_datetime(end)
            duration_minutes = (end_dt - start_dt).total_seconds() / 60

            stage = "asleep"
            if "Deep" in record_type:
                stage = "deep"
            elif "REM" in record_type:
                stage = "rem"
            elif "Core" in record_type or "Light" in record_type:
                stage = "light"
            elif "Awake" in record_type:
                stage = "awake"
            elif "InBed" in record_type:
                stage = "in_bed"

            records.append({
                "date": start_dt.normalize(),
                "stage": stage,
                "duration_minutes": duration_minutes,
            })

        if not records:
            return pd.DataFrame(columns=["date", "total_sleep_minutes", "source"])

        df = pd.DataFrame(records)
        pivot = df.groupby(["date", "stage"])["duration_minutes"].sum().unstack(fill_value=0).reset_index()

        stage_map = {
            "deep": "deep_sleep_minutes",
            "rem": "rem_sleep_minutes",
            "light": "light_sleep_minutes",
            "asleep": "total_sleep_minutes",
            "awake": "awake_minutes",
            "in_bed": "in_bed_minutes",
        }

        for stage, col in stage_map.items():
            if stage in pivot.columns:
                pivot = pivot.rename(columns={stage: col})

        if "total_sleep_minutes" not in pivot.columns:
            sleep_cols = [c for c in ["deep_sleep_minutes", "rem_sleep_minutes", "light_sleep_minutes"] if c in pivot.columns]
            if sleep_cols:
                pivot["total_sleep_minutes"] = pivot[sleep_cols].sum(axis=1)

        pivot["source"] = "apple_health"
        return pivot


def parse_upload(source_type: str, content: bytes) -> pd.DataFrame:
    parsers = {
        "fitbit": FitbitParser.parse,
        "garmin": GarminParser.parse,
        "apple_health": AppleHealthParser.parse,
    }
    parser = parsers.get(source_type)
    if not parser:
        raise ValueError(f"Unsupported source type: {source_type}")
    return parser(content)
