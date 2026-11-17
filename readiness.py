"""Pure pandas readiness baseline. No UI, filesystem, database, or ML access."""
from __future__ import annotations

import pandas as pd

CANONICAL_STATUSES = ("FMC", "PMCM", "PMCS", "NMCS", "NMCM", "DEPOT")
STATUS_CANON = {
    "FMC": "FMC", "MC": "FMC", "FULLY MISSION CAPABLE": "FMC",
    "FULLY_CAPABLE": "FMC", "FULL CAPABLE": "FMC", "MISSION CAPABLE": "FMC",
    "PMC": "PMCM", "PMCM": "PMCM", "PMCS": "PMCS",
    "PARTIALLY MISSION CAPABLE": "PMCM", "PARTIAL CAPABLE": "PMCM",
    "NMCS": "NMCS", "NMC": "NMCS", "NON MISSION CAPABLE SUPPLY": "NMCS",
    "NMC-S": "NMCS", "NMCS (SUPPLY)": "NMCS", "NMCM": "NMCM",
    "DEPOT": "DEPOT", "DM": "DEPOT", "DLM": "DEPOT", "DEPOT MAINT": "DEPOT",
}
CANDIDATE_COLS = {
    "date": ["date", "created_on", "created_on_", "evt_date"],
    "platform": ["platform", "pltf", "pltf_", "ac_type"],
    "tail": ["tail", "tail_num", "tail_num_", "t_num"],
    "status": ["status", "cond", "cond_", "condition"],
    "location": ["location", "base", "station", "location_"],
    "command": ["command", "cmd", "wing", "group", "code_", "cmd_code"],
    "reason": ["reason", "fault", "fault_", "reason_code"],
    "hrs_to_insp": ["hrs_to_insp", "hrs_to_insp_", "hours_to_insp"],
    "hrs_to_phase": ["hrs_to_phase", "hrs_to_phase_", "hours_to_phase"],
}


def normalize_status(values: pd.Series) -> pd.Series:
    """Preserve unknown/null stringification behavior of the legacy application."""
    return values.astype(str).str.upper().str.strip().map(
        lambda value: STATUS_CANON.get(value, value)
    )


def coalesce_columns(events: pd.DataFrame) -> pd.DataFrame:
    """Legacy aliases, date coercion, numeric coercion, and text normalization.

    Column matching ignores case, but intentionally does not trim header spaces.
    Tail identifiers must already be text if leading zeros are to survive.
    """
    result = events.copy()
    columns = {column.lower(): column for column in result.columns}
    rename = {}
    for canonical, aliases in CANDIDATE_COLS.items():
        existing = next((columns[a.lower()] for a in aliases if a.lower() in columns), None)
        if existing is not None and existing != canonical:
            rename[existing] = canonical
    result = result.rename(columns=rename)
    if "date" in result:
        result["date"] = pd.to_datetime(result["date"], errors="coerce")
        result = result[result["date"].notna()]
    for column in ("hrs_to_insp", "hrs_to_phase"):
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    if "status" in result:
        result["status"] = normalize_status(result["status"])
    for column in ("platform", "tail", "location", "command", "reason"):
        if column in result:
            result[column] = result[column].astype(str).str.strip()
    return result


def build_tail_daily_snapshot(events: pd.DataFrame) -> pd.DataFrame:
    """Last non-null column values per tail/day; forward-fill to global last day.

    No backfill before a tail's first event, no extension to wall-clock today,
    and no staleness limit. Call coalesce_columns first for raw/aliased events.
    """
    if not {"date", "tail", "status"}.issubset(events.columns):
        return pd.DataFrame()
    data = events.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data[data["date"].notna()]
    if data.empty:
        return data
    data["status"] = normalize_status(data["status"])
    data["day"] = data["date"].dt.normalize()
    last_day = data["day"].max()
    data = data.sort_values(["tail", "date"])
    frames = []
    # Explicit iteration avoids pandas GroupBy.apply's deprecated inclusion of keys.
    for _, group in data.groupby("tail"):
        daily = group.sort_values("date").groupby("day").last()
        daily = daily.drop(columns=[c for c in ("date", "day") if c in daily])
        days = pd.date_range(daily.index.min(), last_day, freq="D")
        daily = daily.reindex(days).ffill()
        daily.index.name = "date"
        frames.append(daily.reset_index())
    if not frames:
        return pd.DataFrame()
    snapshot = pd.concat(frames, ignore_index=True)
    snapshot["date"] = pd.to_datetime(snapshot["date"]).dt.normalize()
    snapshot["status"] = normalize_status(snapshot["status"])
    return snapshot


def _validate_snapshot(snapshot: pd.DataFrame) -> None:
    """Prevent raw event rows from silently inflating status counts."""
    required = {"date", "tail", "status"}
    if not required.issubset(snapshot):
        raise ValueError("Metrics require date, tail, and status columns")
    if snapshot.duplicated(["date", "tail"]).any():
        raise ValueError("Metrics require one row per date/tail; build a daily snapshot first")


def _metrics(group: pd.DataFrame) -> dict:
    total = group["tail"].nunique()
    status = group["status"]
    fmc = int(status.eq("FMC").sum())
    pmc = int(status.isin(["PMCM", "PMCS"]).sum())
    nmcs = int(status.eq("NMCS").sum())
    nmcm = int(status.eq("NMCM").sum())
    depot = int(status.eq("DEPOT").sum())
    denominator = total - (nmcs + depot)  # NMCM stays in denominator: executed legacy formula.
    return {
        "total_tails": int(total), "fmc_tails": fmc, "pmc_tails": pmc,
        "nmcm_tails": nmcm, "nmcs_tails": nmcs, "depot_tails": depot,
        "svc_pct": (fmc + pmc) / denominator * 100.0 if denominator > 0 else 0.0,
        "avail_pct": (fmc + pmc) / total * 100.0 if total > 0 else 0.0,
    }


def compute_jac_daily_metrics(snapshot: pd.DataFrame) -> pd.DataFrame:
    """Fleet metrics, preserving executed v3_10_2/v3_10_4 formulas."""
    if snapshot.empty:
        return pd.DataFrame()
    _validate_snapshot(snapshot)
    rows = [{"date": day, **_metrics(group)} for day, group in snapshot.groupby("date")
            if group["tail"].nunique() > 0]
    return pd.DataFrame(rows).sort_values("date") if rows else pd.DataFrame()


def compute_command_latest_metrics(snapshot: pd.DataFrame, latest_date) -> pd.DataFrame:
    """Command metrics for the supplied calendar date (not necessarily latest)."""
    if snapshot.empty or "command" not in snapshot:
        return pd.DataFrame()
    _validate_snapshot(snapshot)
    selected = snapshot[snapshot["date"] == pd.to_datetime(latest_date).normalize()]
    rows = [{"command": command, **_metrics(group)}
            for command, group in selected.groupby("command")
            if group["tail"].nunique() > 0]
    return pd.DataFrame(rows).sort_values("command") if rows else pd.DataFrame()
