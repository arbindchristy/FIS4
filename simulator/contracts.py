"""Version 1 tabular contracts, validation and existing-provider adapter."""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

import pandas as pd

import readiness


COMMANDS = ("FICTIONAL_A", "FICTIONAL_B", "FICTIONAL_C", "FICTIONAL_D")
SCHEMAS = {
    "aircraft": ("tail", "command", "initial_hours", "inspection_interval", "initial_hrs_to_insp"),
    "events": ("date", "tail", "status", "command"),
    "operations": ("date", "tail", "flight_hours", "total_hours", "hrs_to_insp",
                   "fault_count", "recurring_fault_count", "active_episode",
                   "episode_age_days", "supply_wait_days", "outstanding_demand"),
    "episodes": ("episode_id", "tail", "kind", "fault_code", "recurring",
                 "opened_at", "closed_at"),
    "actions": ("date", "episode_id", "action"),
}
KINDS = ("FAULT", "INSPECTION", "DEPOT")
ACTIONS = ("OPEN", "PART_REQUEST", "PART_RECEIPT", "CLOSE")


@dataclass(frozen=True)
class SimulationConfig:
    # No wall-clock default: invocation always identifies the observation cutoff.
    as_of: date
    seed: int = 42017
    tails: int = 160
    years: int = 4

    def __post_init__(self):
        if type(self.as_of) is not date or not 2000 <= self.as_of.year <= 2100:
            raise ValueError("as_of must be a date in 2000..2100")
        for name, low, high in (("seed", 0, 2**32 - 1), ("tails", 4, 1600), ("years", 1, 10)):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} outside supported integer bounds")
        if self.tails % 4 or self.tails * self.days > 3_000_000:
            raise ValueError("tails must be divisible by four; maximum 3,000,000 tail-days")

    @property
    def start(self) -> date:
        # Four calendar years, inclusive of cutoff, exclusive of prior anniversary.
        try:
            anniversary = self.as_of.replace(year=self.as_of.year - self.years)
        except ValueError:  # Feb 29 -> Feb 28 in a non-leap anniversary year.
            anniversary = self.as_of.replace(year=self.as_of.year - self.years, day=28)
        return anniversary + timedelta(days=1)

    @property
    def days(self) -> int:
        return (self.as_of - self.start).days + 1


@dataclass
class SyntheticHistory:
    config: SimulationConfig
    aircraft: pd.DataFrame
    events: pd.DataFrame
    operations: pd.DataFrame
    episodes: pd.DataFrame
    actions: pd.DataFrame
    snapshot: pd.DataFrame
    source: Literal["synthetic"] = "synthetic"

    def load_events(self) -> pd.DataFrame:
        """Structural api.providers.DataProvider compatibility, defensive copy."""
        return self.events.copy(deep=True)

    def validate(self) -> None:
        """Reject invalid exports before any downstream consumer uses them."""
        def require(condition, message):
            if not condition:
                raise ValueError(message)

        c = self.config
        require(self.source == "synthetic", "source must be synthetic")
        for name, columns in SCHEMAS.items():
            frame = getattr(self, name)
            require(tuple(frame.columns) == columns, f"{name}: schema mismatch")
        fleet, ops, events, episodes, actions = (
            self.aircraft, self.operations, self.events, self.episodes, self.actions)
        require(len(fleet) == c.tails and fleet["tail"].is_unique, "aircraft cardinality")
        require(fleet["tail"].tolist() == [f"{i:06d}" for i in range(1, c.tails + 1)], "tail identifiers")
        require(set(fleet.command) == set(COMMANDS), "four fictional commands required")
        require((fleet.groupby("command").size() == c.tails // 4).all(), "command balance")
        require((fleet.initial_hours >= 0).all() and (fleet.inspection_interval > 0).all(), "fleet hours")
        require((fleet.initial_hrs_to_insp > 0).all()
                and fleet.initial_hrs_to_insp.le(fleet.inspection_interval).all(), "initial inspection balance")
        days = pd.date_range(c.start, c.as_of)
        expected = pd.MultiIndex.from_product([days, fleet["tail"]], names=["date", "tail"])
        require(pd.MultiIndex.from_frame(ops[["date", "tail"]]).equals(expected), "daily coverage/order")
        require(not ops.isna().any().any(), "null operational features")
        require(events["tail"].isin(fleet["tail"]).all(), "unknown event tail")
        require(not events.duplicated(["date", "tail"]).any(), "conflicting event timestamps")
        require(events.equals(events.sort_values(["date", "tail"]).reset_index(drop=True)), "event ordering")
        require(events.status.isin(readiness.CANONICAL_STATUSES).all(), "unknown status")
        require(events.command.eq(events["tail"].map(fleet.set_index("tail").command)).all(), "event command")
        first_last = events.groupby("tail").date.agg(["min", "max"])
        require(len(first_last) == c.tails and first_last["min"].dt.normalize().eq(days[0]).all()
                and first_last["max"].dt.normalize().eq(days[-1]).all(), "event coverage")
        require(events.date.between(days[0], days[-1] + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)).all(), "event cutoff")
        rebuilt = readiness.build_tail_daily_snapshot(readiness.coalesce_columns(events))
        rebuilt = rebuilt.sort_values(["date", "tail"]).reset_index(drop=True)
        require(self.snapshot.equals(rebuilt), "snapshot must match approved engine")
        require(pd.MultiIndex.from_frame(self.snapshot[["date", "tail"]]).equals(expected), "snapshot coverage")
        joined = ops.merge(self.snapshot, on=["date", "tail"], validate="one_to_one")
        initial = ops["tail"].map(fleet.set_index("tail").initial_hours)
        require(((ops.groupby("tail").flight_hours.cumsum() + initial - ops.total_hours).abs() < 1e-7).all(), "accumulated hours")
        require(ops.flight_hours.between(0, 6).all() and (ops.hrs_to_insp >= 0).all(), "hour bounds")
        require(joined.loc[joined.status.isin(["NMCS", "NMCM", "DEPOT"]), "flight_hours"].eq(0).all(), "grounded flight")
        require(episodes.episode_id.is_unique and episodes["tail"].isin(fleet["tail"]).all(), "episode keys")
        require(episodes.kind.isin(KINDS).all() and actions.action.isin(ACTIONS).all(), "episode/action kinds")
        require(actions.episode_id.isin(episodes.episode_id).all(), "action foreign key")
        require(actions.equals(actions.sort_values(["date", "episode_id", "action"]).reset_index(drop=True)), "action ordering")
        require(not actions.duplicated(["episode_id", "action"]).any(), "duplicate lifecycle action")
        require(actions.date.between(days[0], days[-1] + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)).all(), "action cutoff")
        timeline = actions.pivot(index="episode_id", columns="action", values="date").reindex(episodes.episode_id)
        require(timeline.OPEN.notna().all() and timeline.OPEN.reset_index(drop=True).equals(episodes.opened_at), "episode open")
        closed = timeline.reindex(columns=["CLOSE"])["CLOSE"].reset_index(drop=True)
        require(closed.equals(episodes.closed_at), "episode close")
        require((episodes.closed_at.isna() | (episodes.closed_at > episodes.opened_at)).all(), "episode timing")
        for _, group in episodes.groupby("tail", sort=False):
            require(group.opened_at.is_monotonic_increasing, "episode ordering")
            if len(group) > 1:
                require((group.closed_at.iloc[:-1].reset_index(drop=True) < group.opened_at.iloc[1:].reset_index(drop=True)).all(), "overlapping episodes")
        request = timeline.reindex(columns=["PART_REQUEST"])["PART_REQUEST"]
        receipt = timeline.reindex(columns=["PART_RECEIPT"])["PART_RECEIPT"]
        close = timeline.reindex(columns=["CLOSE"])["CLOSE"]
        require((request.isna() | request.ge(timeline.OPEN)).all(), "request before fault")
        require((receipt.isna() | (request.notna() & receipt.gt(request))).all(), "receipt before demand")
        require((close.isna() | request.isna() | (receipt.notna() & close.gt(receipt))).all(), "repair before receipt")
        require((request.isna() | episodes.set_index("episode_id").kind.eq("FAULT")).all(), "non-fault supply")
        require(episodes.loc[episodes.kind.eq("FAULT"), "fault_code"].str.startswith("FICTIONAL_").all(), "fault codes")
        require(episodes.loc[~episodes.kind.eq("FAULT"), "fault_code"].eq("").all(), "non-fault code")
        require((~episodes.recurring | episodes.kind.eq("FAULT")).all(), "non-fault recurrence")
        by_id = episodes.set_index("episode_id")
        for tail, group in ops.groupby("tail", sort=False):
            group = group.reset_index(drop=True)
            tail_episodes = episodes[episodes["tail"].eq(tail)]
            expected_active = pd.Series("", index=group.index)
            resets = set()
            prior_codes = set()
            for ep in tail_episodes.itertuples(index=False):
                opened = ep.opened_at.normalize()
                closed_day = ep.closed_at.normalize() if pd.notna(ep.closed_at) else days[-1] + pd.Timedelta(days=1)
                expected_active.loc[group.date.ge(opened) & group.date.lt(closed_day)] = ep.episode_id
                if ep.kind in ("INSPECTION", "DEPOT") and pd.notna(ep.closed_at):
                    resets.add(closed_day)
                if ep.kind == "INSPECTION":
                    prior_balance = group.loc[group.date.lt(opened), "hrs_to_insp"]
                    require(not prior_balance.empty and prior_balance.iloc[-1] == 0, "inspection before due")
                if ep.kind == "FAULT":
                    require(not ep.recurring or ep.fault_code in prior_codes, "recurrence without prior fault")
                    prior_codes.add(ep.fault_code)
            require(group.active_episode.equals(expected_active), "active episode coverage")
            previous = group.hrs_to_insp.shift(1)
            previous.iloc[0] = float(fleet.set_index("tail").loc[tail, "initial_hrs_to_insp"])
            expected_remaining = previous - group.flight_hours
            reset_mask = group.date.isin(resets)
            expected_remaining.loc[reset_mask] = float(fleet.set_index("tail").loc[tail, "inspection_interval"]) - group.loc[reset_mask, "flight_hours"]
            require((group.hrs_to_insp - expected_remaining).abs().lt(1e-7).all(), "inspection progression")
            require(group.hrs_to_insp.le(float(fleet.set_index("tail").loc[tail, "inspection_interval"])).all(), "inspection interval")
            faults = tail_episodes[tail_episodes.kind.eq("FAULT")]
            for field, subset in (("fault_count", faults), ("recurring_fault_count", faults[faults.recurring])):
                expected_counts = group.date.map(subset.opened_at.dt.normalize().value_counts()).fillna(0).cumsum()
                require(group[field].eq(expected_counts).all(), "observed fault counts")
        active_rows = joined[joined.active_episode.ne("")].copy()
        if not active_rows.empty:
            active_rows = active_rows.join(by_id, on="active_episode", rsuffix="_episode", validate="many_to_one")
            age = (active_rows.date - active_rows.opened_at.dt.normalize()).dt.days
            require(active_rows.episode_age_days.eq(age).all(), "observed episode age")
            requested = active_rows.active_episode.map(request)
            received = active_rows.active_episode.map(receipt)
            waiting = requested.notna() & (received.isna() | received.dt.normalize().gt(active_rows.date))
            require(active_rows.outstanding_demand.eq(waiting.astype(int)).all(), "outstanding supply")
            require(active_rows.supply_wait_days.eq(age.where(waiting, 0)).all(), "observed supply age")
            require(active_rows.loc[waiting, "status"].isin(["PMCS", "NMCS"]).all(), "waiting status")
            require(active_rows.loc[~waiting & active_rows.kind.eq("FAULT"), "status"].isin(["PMCM", "NMCM"]).all(), "repair status")
            require(active_rows.loc[active_rows.kind.eq("DEPOT"), "status"].eq("DEPOT").all(), "depot status")
            require(active_rows.loc[active_rows.kind.eq("INSPECTION"), "status"].eq("NMCM").all(), "inspection status")
        healthy = joined[joined.active_episode.eq("")]
        require(healthy.status.eq("FMC").all() and healthy.episode_age_days.eq(0).all()
                and healthy.supply_wait_days.eq(0).all() and healthy.outstanding_demand.eq(0).all(), "healthy state")
        # A persistent major/minor fault can change only from supply to repair,
        # never independently toggle severity or return to waiting.
        active_statuses = joined[joined.active_episode.ne("")].groupby("active_episode").status.agg(list)
        allowed = {("NMCS", "NMCM"), ("PMCS", "PMCM")}
        for statuses in active_statuses:
            compressed = [s for i, s in enumerate(statuses) if i == 0 or s != statuses[i - 1]]
            require(len(compressed) == 1 or tuple(compressed) in allowed, "invalid persistent transition")

    def features_at(self, day: date) -> pd.DataFrame:
        """End-of-day observed features only; never join eventual episode outcomes."""
        if type(day) is not date or not self.config.start <= day <= self.config.as_of:
            raise ValueError("feature date outside generated history")
        stamp = pd.Timestamp(day)
        return self.operations[self.operations.date.eq(stamp)].merge(
            self.snapshot[self.snapshot.date.eq(stamp)], on=["date", "tail"], validate="one_to_one")
