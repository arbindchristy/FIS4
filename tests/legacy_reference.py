"""Read-only isolation of explicitly reviewed calculation definitions, never app import."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

ROOT = Path(r"C:\AI\Projects\fleet_cpi_suite")
REFERENCES = {
    "streamlit_sql_portal_v3_10_2.py": "05bb1c077ec77d5b21bc7ce53fe0c8c8bb7188bbe8356099bc9fbe75e2b8dce7",
    "streamlit_sql_portal_v3_10_4.py": "6b1ef3451ec9a47203cf96d1cd7a83bb872ed64bd3bce523c9c744ca4be06980",
}
MISSING_REFERENCE = "streamlit_sql_portal_v3_10_5_corrected.py"
FUNCTIONS = {
    "_first_existing", "coalesce_columns", "build_tail_daily_snapshot",
    "compute_jac_daily_metrics", "compute_command_latest_metrics",
}
CONSTANTS = {
    "CANDIDATE_COLS", "STATUS_CANON", "FMC_SET", "PMC_SET", "NMCS_SET",
    "NMCM_SET", "DEPOT_SET",
}


def load_reference(name: str) -> dict:
    path = ROOT / name
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REFERENCES[name]:
        raise ValueError(f"Reference changed: review and re-pin {name} before execution")
    source = raw.decode("utf-8-sig")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        if name != "streamlit_sql_portal_v3_10_4.py":
            raise
        # Its UI syntax error is after all readiness functions. Prefix is parsed only.
        tree = ast.parse(source.split("# Sidebar", 1)[0], filename=str(path))
    selected = []
    found = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS:
            if node.decorator_list:
                raise ValueError("Unexpected decorated reference function")
            selected.append(node)
            found.add(node.name)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in CONSTANTS:
                ast.literal_eval(node.value)  # Constants must be literal data.
                selected.append(node)
                found.add(target.id)
    if found != FUNCTIONS | CONSTANTS:
        raise ValueError(f"Incomplete reference extraction: {found}")
    namespace = {"pd": pd, "Iterable": Iterable, "Optional": Optional}
    isolated = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    # Only hash-pinned, reviewed pure calculation definitions are compiled/executed.
    # No imports, top-level UI, config, CSV, SQL, or model-loading statements selected.
    exec(compile(isolated, str(path), "exec"), namespace)
    return namespace
