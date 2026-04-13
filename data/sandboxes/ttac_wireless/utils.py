#!/usr/bin/env python
# -*-coding:utf-8 -*-


import json
import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from _types import Scenario
from dateutil import parser


def load_scenarios(config, split="test"):
    with open(f"./{config}/{split}.json", "r", encoding="utf-8") as f:
        raw_scenarios = json.load(f)

    if not raw_scenarios:
        raise RuntimeError(
            f"No scenarios loaded. Check ./{config}/test.json or DOWNLOAD_FROM_REMOTE."
        )

    return [Scenario.model_validate(s) for s in raw_scenarios]


def df_first_or_none(df: pd.DataFrame) -> dict[str, Any] | None:
    if df is None or df.empty:
        return None
    return df.iloc[0].to_dict()


def df_all_or_none(df: pd.DataFrame) -> dict[str, Any] | None:
    if df is None or df.empty:
        return None
    return df.to_csv(index=False, sep="|")


def normalize_time(ts: str) -> datetime:
    dt = parser.parse(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def get_fields_at_time(
    df: pd.DataFrame, user_input_time: str, fields: list[str]
) -> pd.DataFrame:
    target_time = normalize_time(user_input_time)
    tmp = df.copy()
    tmp["NormalizedTime"] = tmp["Timestamp"].apply(normalize_time)
    return tmp.loc[tmp["NormalizedTime"] == target_time, fields]


def get_fields_before_time(
    df: pd.DataFrame, user_input_time: str, fields: list[str]
) -> pd.DataFrame:
    target_time = normalize_time(user_input_time)
    tmp = df.copy()
    tmp["NormalizedTime"] = tmp["Timestamp"].apply(normalize_time)
    return tmp.loc[tmp["NormalizedTime"] <= target_time, fields]


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}
