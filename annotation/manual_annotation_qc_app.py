from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

APP_TITLE = "MammalWeb Random-50 QC Review"
PROTOCOL_VERSION = "1.1"

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "sampling_outputs"
QC_ROOT = BASE_DIR / "annotation_quality_control_outputs"

DATABASE_PATH = OUTPUT_DIR / "manual_annotations.sqlite"
EXPORT_PATH = OUTPUT_DIR / "manual_annotations.csv"

PROTOCOL_CANDIDATES = [
    BASE_DIR / "manual_annotation_protocol_v1_1.md",
    BASE_DIR / "manual_annotation_protocol.md",
]

REQUIRED_QC_COLUMNS = {
    "annotation_queue_id",
    "annotation_image_url",
}

PRESENCE_OPTIONS = [
    "— Select —",
    "Yes",
    "No",
    "Uncertain",
]

QUALITY_OPTIONS = [
    "— Select —",
    "Clear",
    "Difficult but usable",
    "Unusable",
]

HUMAN_RECOGNISABILITY_OPTIONS = [
    "— Not applicable —",
    "0 — Not recognisable",
    "1 — Potentially recognisable",
    "2 — Clearly recognisable",
]

CHILD_VULNERABLE_OPTIONS = [
    "— Not applicable —",
    "No",
    "Yes",
    "Uncertain",
]

HUMAN_PRIVACY_OPTIONS = [
    "— Not applicable —",
    "0 — None or minimal",
    "1 — Moderate",
    "2 — High",
]

SAFEGUARDING_OPTIONS = [
    "— Not applicable —",
    "0 — None apparent",
    "1 — Possible concern",
    "2 — Clear concern",
]

VEHICLE_IDENTIFIABILITY_OPTIONS = [
    "— Not applicable —",
    "0 — Not identifiable",
    "1 — Potentially identifiable",
    "2 — Clearly identifiable",
]

VEHICLE_PRIVACY_OPTIONS = [
    "— Not applicable —",
    "0 — None or minimal",
    "1 — Moderate",
    "2 — High",
]

EDITABLE_FIELDS = [
    "manual_human_present",
    "manual_animal_present",
    "manual_vehicle_present",
    "annotation_quality",
    "human_recognisability",
    "child_or_vulnerable_person_visible",
    "human_privacy_risk",
    "safeguarding_risk",
    "vehicle_identifiability",
    "vehicle_privacy_risk",
    "notes",
    "needs_review",
]


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_timestamp(value: datetime | None = None) -> str:
    timestamp = value or utc_now()
    return timestamp.isoformat(timespec="seconds")


def safe_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def numeric_score(label: str) -> int | None:
    if not label or label.startswith("—"):
        return None
    return int(label.split("—", maxsplit=1)[0].strip())


def score_label(value: Any, options: list[str]) -> str:
    if value is None or pd.isna(value):
        return options[0]
    try:
        score = int(value)
    except (TypeError, ValueError):
        return options[0]

    prefix = f"{score} "
    return next((option for option in options if option.startswith(prefix)), options[0])


def option_index(options: list[str], value: Any) -> int:
    if value is None or pd.isna(value):
        return 0
    text = str(value)
    try:
        return options.index(text)
    except ValueError:
        return 0


def protocol_path() -> Path | None:
    return next((path for path in PROTOCOL_CANDIDATES if path.exists()), None)


def discover_qc_samples() -> list[Path]:
    if not QC_ROOT.exists():
        return []
    paths = list(QC_ROOT.glob("qc_run_*/normal_completed_qc_sample_50.csv"))
    return sorted(paths, key=lambda path: path.stat().st_mtime, reverse=True)


@st.cache_data(show_spinner=False)
def load_qc_queue(path: str) -> pd.DataFrame:
    queue = pd.read_csv(path, low_memory=False)
    queue.columns = queue.columns.str.strip()

    missing = REQUIRED_QC_COLUMNS - set(queue.columns)
    if missing:
        raise ValueError(
            "QC sample is missing required columns: " + ", ".join(sorted(missing))
        )

    queue["annotation_queue_id"] = queue["annotation_queue_id"].astype("string").str.strip()
    queue["annotation_image_url"] = queue["annotation_image_url"].astype("string").str.strip()

    if queue["annotation_queue_id"].isna().any():
        raise ValueError("QC sample contains missing annotation_queue_id values.")
    if queue["annotation_queue_id"].duplicated().any():
        raise ValueError("QC sample contains duplicate annotation_queue_id values.")
    if queue["annotation_image_url"].isna().any():
        raise ValueError("QC sample contains missing annotation_image_url values.")

    return queue.reset_index(drop=True)


# ---------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------

def connect_database() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def load_annotation(annotation_queue_id: str) -> dict[str, Any] | None:
    with connect_database() as connection:
        row = connection.execute(
            "SELECT * FROM annotations WHERE annotation_queue_id = ?",
            (annotation_queue_id,),
        ).fetchone()
    return dict(row) if row else None


def load_all_annotations() -> pd.DataFrame:
    with connect_database() as connection:
        return pd.read_sql_query("SELECT * FROM annotations", connection)


def export_annotations() -> None:
    annotations = load_all_annotations().sort_values("annotation_queue_id", kind="stable")
    temporary_path = EXPORT_PATH.with_suffix(".tmp.csv")
    annotations.to_csv(temporary_path, index=False)
    os.replace(temporary_path, EXPORT_PATH)


def update_existing_annotation(annotation_queue_id: str, values: dict[str, Any]) -> None:
    """Update only QC-editable fields on an existing row. Never insert a new annotation."""
    assignments = ", ".join(f"{column} = ?" for column in EDITABLE_FIELDS)
    parameters = [values.get(column) for column in EDITABLE_FIELDS]
    parameters.append(iso_timestamp())
    parameters.append(annotation_queue_id)

    with connect_database() as connection:
        existing = connection.execute(
            "SELECT 1 FROM annotations WHERE annotation_queue_id = ?",
            (annotation_queue_id,),
        ).fetchone()
        if existing is None:
            raise ValueError(
                f"Cannot QC-update {annotation_queue_id}: no existing annotation row was found."
            )

        cursor = connection.execute(
            f"""
            UPDATE annotations
            SET {assignments}, updated_at = ?
            WHERE annotation_queue_id = ?
            """,
            parameters,
        )
        if cursor.rowcount != 1:
            raise RuntimeError(
                f"Expected exactly one row to update for {annotation_queue_id}; got {cursor.rowcount}."
            )

    export_annotations()


# ---------------------------------------------------------------------
# QC log
# ---------------------------------------------------------------------

def qc_log_path(sample_path: Path) -> Path:
    return sample_path.parent / "normal_qc_review_log.csv"


def load_qc_log(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "annotation_queue_id",
                "qc_reviewed_at",
                "changed",
                "changed_fields",
            ]
        )
    return pd.read_csv(path, dtype={"annotation_queue_id": "string"})


def save_qc_log_entry(
    path: Path,
    annotation_queue_id: str,
    changed_fields: list[str],
) -> None:
    log = load_qc_log(path)
    log = log.loc[log["annotation_queue_id"].astype(str) != annotation_queue_id].copy()

    entry = pd.DataFrame(
        [
            {
                "annotation_queue_id": annotation_queue_id,
                "qc_reviewed_at": iso_timestamp(),
                "changed": int(bool(changed_fields)),
                "changed_fields": "; ".join(changed_fields),
            }
        ]
    )
    log = pd.concat([log, entry], ignore_index=True)
    log = log.sort_values("annotation_queue_id", kind="stable")

    temporary_path = path.with_suffix(".tmp.csv")
    log.to_csv(temporary_path, index=False)
    os.replace(temporary_path, path)


# ---------------------------------------------------------------------
# Form logic
# ---------------------------------------------------------------------

def validate_form(
    quality: str,
    human: str,
    animal: str,
    vehicle: str,
    human_recognisability_label: str,
    child_vulnerable: str,
    human_privacy_label: str,
    safeguarding_label: str,
    vehicle_identifiability_label: str,
    vehicle_privacy_label: str,
) -> list[str]:
    errors: list[str] = []

    if quality == "— Select —":
        errors.append("Select image quality.")

    if quality != "Unusable":
        if human == "— Select —":
            errors.append("Select the human-presence label.")
        if animal == "— Select —":
            errors.append("Select the animal-presence label.")
        if vehicle == "— Select —":
            errors.append("Select the vehicle-presence label.")

    if human == "Yes":
        if human_recognisability_label.startswith("—"):
            errors.append("Select human recognisability.")
        if child_vulnerable.startswith("—"):
            errors.append("Select whether a child or vulnerable person is visible.")
        if human_privacy_label.startswith("—"):
            errors.append("Select human privacy risk.")
        if safeguarding_label.startswith("—"):
            errors.append("Select safeguarding risk.")

    if vehicle == "Yes":
        if vehicle_identifiability_label.startswith("—"):
            errors.append("Select vehicle identifiability.")
        if vehicle_privacy_label.startswith("—"):
            errors.append("Select vehicle privacy risk.")

    return errors


def calculate_needs_review(
    human: str,
    animal: str,
    vehicle: str,
    quality: str,
    human_recognisability: int | None,
    child_vulnerable: str | None,
    human_privacy: int | None,
    safeguarding: int | None,
    vehicle_privacy: int | None,
) -> bool:
    return any(
        [
            "Uncertain" in {human, animal, vehicle},
            quality == "Unusable",
            human_recognisability in {1, 2},
            child_vulnerable in {"Yes", "Uncertain"},
            human_privacy in {1, 2},
            safeguarding in {1, 2},
            vehicle_privacy == 2,
        ]
    )


def normalise_for_compare(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def changed_fields(existing: dict[str, Any], proposed: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    for field in EDITABLE_FIELDS:
        if normalise_for_compare(existing.get(field)) != normalise_for_compare(proposed.get(field)):
            changed.append(field)
    return changed


def move_sequentially(queue_ids: list[str], current_id: str, offset: int) -> str:
    current_index = queue_ids.index(current_id)
    new_index = max(0, min(len(queue_ids) - 1, current_index + offset))
    return queue_ids[new_index]


def next_not_reviewed_id(
    queue_ids: list[str],
    reviewed_ids: set[str],
    current_id: str,
) -> str:
    current_index = queue_ids.index(current_id)
    ordered = queue_ids[current_index + 1 :] + queue_ids[: current_index + 1]
    for queue_id in ordered:
        if queue_id not in reviewed_ids:
            return queue_id
    return current_id


def set_current_id(queue_id: str) -> None:
    st.session_state.current_qc_queue_id = queue_id


# ---------------------------------------------------------------------
# Streamlit page
# ---------------------------------------------------------------------

st.set_page_config(page_title=APP_TITLE, page_icon="✅", layout="wide")
st.title(APP_TITLE)
st.caption(
    "Review only the preselected random 50 QC images. Existing annotations are pre-filled; "
    "saving updates the same original row and never creates a duplicate."
)

if not DATABASE_PATH.exists():
    st.error(f"Annotation database not found at `{DATABASE_PATH}`")
    st.stop()

sample_paths = discover_qc_samples()
if not sample_paths:
    st.error(
        "No `normal_completed_qc_sample_50.csv` was found under "
        "`annotation_quality_control_outputs/qc_run_*/`."
    )
    st.stop()

with st.sidebar:
    st.header("QC session")

    sample_labels = [str(path.relative_to(BASE_DIR)) for path in sample_paths]
    selected_label = st.selectbox(
        "QC sample",
        options=sample_labels,
        index=0,
        help="The newest QC run is selected by default.",
    )
    sample_path = BASE_DIR / selected_label

    selected_protocol_path = protocol_path()
    st.caption(f"Protocol version: {PROTOCOL_VERSION}")
    if selected_protocol_path:
        with st.expander("Open annotation protocol"):
            st.markdown(selected_protocol_path.read_text(encoding="utf-8"))

try:
    qc_queue = load_qc_queue(str(sample_path))
except Exception as error:
    st.exception(error)
    st.stop()

active_ids = qc_queue["annotation_queue_id"].astype(str).tolist()
if not active_ids:
    st.error("The selected QC sample is empty.")
    st.stop()

# Confirm every QC ID already exists in the annotation DB.
all_annotations = load_all_annotations()
database_ids = set(all_annotations["annotation_queue_id"].astype(str))
missing_from_db = [queue_id for queue_id in active_ids if queue_id not in database_ids]
if missing_from_db:
    st.error(
        "The QC app refuses to create new annotation rows. These QC IDs are missing from the "
        f"database: {', '.join(missing_from_db[:10])}"
    )
    st.stop()

log_path = qc_log_path(sample_path)
qc_log = load_qc_log(log_path)
reviewed_ids = set(qc_log["annotation_queue_id"].dropna().astype(str))
reviewed_ids &= set(active_ids)

if (
    st.session_state.get("qc_sample_path") != str(sample_path)
    or st.session_state.get("current_qc_queue_id") not in active_ids
):
    st.session_state.qc_sample_path = str(sample_path)
    first_id = next((queue_id for queue_id in active_ids if queue_id not in reviewed_ids), active_ids[0])
    set_current_id(first_id)

current_id = str(st.session_state.current_qc_queue_id)
current_position = active_ids.index(current_id)
current_row = qc_queue.iloc[current_position]
existing = load_annotation(current_id)
if existing is None:
    st.error(f"Existing annotation not found for `{current_id}`.")
    st.stop()

reviewed_count = len(reviewed_ids)
changed_count = (
    int(pd.to_numeric(qc_log.get("changed", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    if not qc_log.empty
    else 0
)

metric_columns = st.columns(4)
metric_columns[0].metric("QC reviewed", f"{reviewed_count} / {len(active_ids)}")
metric_columns[1].metric("Changed", f"{changed_count}")
metric_columns[2].metric("Unchanged", f"{max(0, reviewed_count - changed_count)}")
metric_columns[3].metric("Current", f"{current_position + 1} / {len(active_ids)}")

st.progress(
    reviewed_count / len(active_ids),
    text=f"{reviewed_count} of {len(active_ids)} random QC images reviewed",
)

navigation_columns = st.columns([1, 1, 1.4, 2.2])
if navigation_columns[0].button("← Previous", width="stretch"):
    set_current_id(move_sequentially(active_ids, current_id, -1))
    st.rerun()

if navigation_columns[1].button("Next →", width="stretch"):
    set_current_id(move_sequentially(active_ids, current_id, 1))
    st.rerun()

if navigation_columns[2].button("Next not reviewed", width="stretch"):
    set_current_id(next_not_reviewed_id(active_ids, reviewed_ids, current_id))
    st.rerun()

jump_id = navigation_columns[3].selectbox(
    "Jump to QC annotation ID",
    options=active_ids,
    index=current_position,
    label_visibility="collapsed",
)
if jump_id != current_id:
    set_current_id(str(jump_id))
    st.rerun()

already_reviewed = current_id in reviewed_ids
status_text = "QC reviewed" if already_reviewed else "not QC reviewed"
st.subheader(f"{current_id} · {status_text}")

image_url = str(current_row["annotation_image_url"])
try:
    st.image(image_url, width="stretch")
except Exception as error:
    st.error("The image could not be displayed in the app.")
    st.exception(error)

st.markdown(f"[Open the full-resolution image in a new tab]({image_url})")

with st.expander("Image identifiers", expanded=False):
    identifier_columns = [
        column
        for column in ["annotation_queue_id", "photo_id", "sequence_id", "site_id", "filename"]
        if column in current_row.index
    ]
    st.dataframe(
        pd.DataFrame(
            {
                "field": identifier_columns,
                "value": [current_row[column] for column in identifier_columns],
            }
        ),
        hide_index=True,
        width="stretch",
    )

existing_human = existing.get("manual_human_present")
existing_animal = existing.get("manual_animal_present")
existing_vehicle = existing.get("manual_vehicle_present")
existing_quality = existing.get("annotation_quality")

with st.form(key=f"qc_form_{current_id}", clear_on_submit=False, enter_to_submit=False):
    st.subheader("Review existing labels")
    core_columns = st.columns(4)

    quality = core_columns[0].selectbox(
        "Image quality",
        QUALITY_OPTIONS,
        index=option_index(QUALITY_OPTIONS, existing_quality),
    )
    human = core_columns[1].selectbox(
        "Human present",
        PRESENCE_OPTIONS,
        index=option_index(PRESENCE_OPTIONS, existing_human),
    )
    animal = core_columns[2].selectbox(
        "Animal present",
        PRESENCE_OPTIONS,
        index=option_index(PRESENCE_OPTIONS, existing_animal),
    )
    vehicle = core_columns[3].selectbox(
        "Vehicle present",
        PRESENCE_OPTIONS,
        index=option_index(PRESENCE_OPTIONS, existing_vehicle),
    )

    st.caption(
        "When Image quality is Unusable, all three presence labels are saved as Uncertain."
    )

    with st.expander(
        "Human-specific labels — complete only when Human = Yes",
        expanded=human == "Yes",
    ):
        human_columns = st.columns(4)
        human_recognisability_label = human_columns[0].selectbox(
            "Human recognisability",
            HUMAN_RECOGNISABILITY_OPTIONS,
            index=option_index(
                HUMAN_RECOGNISABILITY_OPTIONS,
                score_label(existing.get("human_recognisability"), HUMAN_RECOGNISABILITY_OPTIONS),
            ),
        )
        child_vulnerable = human_columns[1].selectbox(
            "Child/vulnerable person visible",
            CHILD_VULNERABLE_OPTIONS,
            index=option_index(
                CHILD_VULNERABLE_OPTIONS,
                existing.get("child_or_vulnerable_person_visible"),
            ),
        )
        human_privacy_label = human_columns[2].selectbox(
            "Human privacy risk",
            HUMAN_PRIVACY_OPTIONS,
            index=option_index(
                HUMAN_PRIVACY_OPTIONS,
                score_label(existing.get("human_privacy_risk"), HUMAN_PRIVACY_OPTIONS),
            ),
        )
        safeguarding_label = human_columns[3].selectbox(
            "Safeguarding risk",
            SAFEGUARDING_OPTIONS,
            index=option_index(
                SAFEGUARDING_OPTIONS,
                score_label(existing.get("safeguarding_risk"), SAFEGUARDING_OPTIONS),
            ),
        )
        st.caption(
            "A child or vulnerable person can be visible while safeguarding risk remains 0."
        )

    with st.expander(
        "Vehicle-specific labels — complete only when Vehicle = Yes",
        expanded=vehicle == "Yes",
    ):
        vehicle_columns = st.columns(2)
        vehicle_identifiability_label = vehicle_columns[0].selectbox(
            "Vehicle identifiability",
            VEHICLE_IDENTIFIABILITY_OPTIONS,
            index=option_index(
                VEHICLE_IDENTIFIABILITY_OPTIONS,
                score_label(existing.get("vehicle_identifiability"), VEHICLE_IDENTIFIABILITY_OPTIONS),
            ),
        )
        vehicle_privacy_label = vehicle_columns[1].selectbox(
            "Vehicle privacy risk",
            VEHICLE_PRIVACY_OPTIONS,
            index=option_index(
                VEHICLE_PRIVACY_OPTIONS,
                score_label(existing.get("vehicle_privacy_risk"), VEHICLE_PRIVACY_OPTIONS),
            ),
        )
        st.caption(
            "A readable plate on an ordinary public road is usually identifiability 2 and privacy risk 1."
        )

    notes = st.text_area(
        "Notes — optional",
        value=existing.get("notes") or "",
        height=90,
        placeholder="Use only for unusual or ambiguous decisions.",
    )

    save_review = st.form_submit_button(
        "Save QC review and next",
        type="primary",
        width="stretch",
    )

if save_review:
    errors = validate_form(
        quality=quality,
        human=human,
        animal=animal,
        vehicle=vehicle,
        human_recognisability_label=human_recognisability_label,
        child_vulnerable=child_vulnerable,
        human_privacy_label=human_privacy_label,
        safeguarding_label=safeguarding_label,
        vehicle_identifiability_label=vehicle_identifiability_label,
        vehicle_privacy_label=vehicle_privacy_label,
    )
    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    if quality == "Unusable":
        human = "Uncertain"
        animal = "Uncertain"
        vehicle = "Uncertain"

    if human == "Yes":
        human_recognisability = numeric_score(human_recognisability_label)
        child_vulnerable_value = child_vulnerable
        human_privacy = numeric_score(human_privacy_label)
        safeguarding = numeric_score(safeguarding_label)
    else:
        human_recognisability = None
        child_vulnerable_value = None
        human_privacy = None
        safeguarding = None

    if vehicle == "Yes":
        vehicle_identifiability = numeric_score(vehicle_identifiability_label)
        vehicle_privacy = numeric_score(vehicle_privacy_label)
    else:
        vehicle_identifiability = None
        vehicle_privacy = None

    needs_review = calculate_needs_review(
        human=human,
        animal=animal,
        vehicle=vehicle,
        quality=quality,
        human_recognisability=human_recognisability,
        child_vulnerable=child_vulnerable_value,
        human_privacy=human_privacy,
        safeguarding=safeguarding,
        vehicle_privacy=vehicle_privacy,
    )

    proposed = {
        "manual_human_present": human,
        "manual_animal_present": animal,
        "manual_vehicle_present": vehicle,
        "annotation_quality": quality,
        "human_recognisability": human_recognisability,
        "child_or_vulnerable_person_visible": child_vulnerable_value,
        "human_privacy_risk": human_privacy,
        "safeguarding_risk": safeguarding,
        "vehicle_identifiability": vehicle_identifiability,
        "vehicle_privacy_risk": vehicle_privacy,
        "notes": safe_text(notes),
        "needs_review": int(needs_review),
    }

    fields_changed = changed_fields(existing, proposed)

    if fields_changed:
        update_existing_annotation(current_id, proposed)

    save_qc_log_entry(log_path, current_id, fields_changed)

    refreshed_log = load_qc_log(log_path)
    refreshed_reviewed_ids = set(refreshed_log["annotation_queue_id"].dropna().astype(str))
    next_id = next_not_reviewed_id(active_ids, refreshed_reviewed_ids, current_id)

    if len(refreshed_reviewed_ids & set(active_ids)) >= len(active_ids):
        st.success("All 50 random QC images have been reviewed.")
        st.rerun()
    else:
        set_current_id(next_id)
        st.rerun()

with st.sidebar:
    st.divider()
    st.caption(f"QC log: `{log_path.relative_to(BASE_DIR)}`")
    st.caption(
        "This QC app only UPDATEs existing annotation rows. It does not load the master sampling key, "
        "MegaDetector confidence scores, or create repeat annotations."
    )
