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

APP_TITLE = "MammalWeb Manual Annotation"
PROTOCOL_VERSION = "1.1"
PILOT_SIZE = 50

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "sampling_outputs"

QUEUE_PATH = OUTPUT_DIR / "blinded_manual_annotation_queue.csv"
DATABASE_PATH = OUTPUT_DIR / "manual_annotations.sqlite"
EXPORT_PATH = OUTPUT_DIR / "manual_annotations.csv"

PROTOCOL_CANDIDATES = [
    BASE_DIR / "manual_annotation_protocol_v1_1.md",
    BASE_DIR / "manual_annotation_protocol.md",
]

REQUIRED_QUEUE_COLUMNS = {
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


# ---------------------------------------------------------------------
# Basic utilities
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


def score_label(
    value: Any,
    options: list[str],
) -> str:
    if value is None or pd.isna(value):
        return options[0]

    try:
        score = int(value)
    except (TypeError, ValueError):
        return options[0]

    prefix = f"{score} "
    return next(
        (
            option
            for option in options
            if option.startswith(prefix)
        ),
        options[0],
    )


def option_index(
    options: list[str],
    value: Any,
) -> int:
    if value is None or pd.isna(value):
        return 0

    text = str(value)
    try:
        return options.index(text)
    except ValueError:
        return 0


def protocol_path() -> Path | None:
    return next(
        (
            path
            for path in PROTOCOL_CANDIDATES
            if path.exists()
        ),
        None,
    )


# ---------------------------------------------------------------------
# Queue loading
# ---------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_queue(path: str) -> pd.DataFrame:
    queue = pd.read_csv(path, low_memory=False)

    queue.columns = queue.columns.str.strip()

    missing_columns = REQUIRED_QUEUE_COLUMNS - set(queue.columns)
    if missing_columns:
        raise ValueError(
            "The annotation queue is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    queue["annotation_queue_id"] = (
        queue["annotation_queue_id"]
        .astype("string")
        .str.strip()
    )

    queue["annotation_image_url"] = (
        queue["annotation_image_url"]
        .astype("string")
        .str.strip()
    )

    if queue["annotation_queue_id"].isna().any():
        raise ValueError(
            "The queue contains missing annotation_queue_id values."
        )

    if queue["annotation_queue_id"].duplicated().any():
        raise ValueError(
            "The queue contains duplicated annotation_queue_id values."
        )

    if queue["annotation_image_url"].isna().any():
        raise ValueError(
            "The queue contains missing annotation_image_url values."
        )

    return queue.reset_index(drop=True)


# ---------------------------------------------------------------------
# SQLite persistence
# ---------------------------------------------------------------------

def connect_database() -> sqlite3.Connection:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
    )
    connection.row_factory = sqlite3.Row
    return connection


def initialise_database() -> None:
    with connect_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS annotations (
                annotation_queue_id TEXT PRIMARY KEY,
                annotation_status TEXT NOT NULL,
                manual_human_present TEXT,
                manual_animal_present TEXT,
                manual_vehicle_present TEXT,
                annotation_quality TEXT,
                human_recognisability INTEGER,
                child_or_vulnerable_person_visible TEXT,
                human_privacy_risk INTEGER,
                safeguarding_risk INTEGER,
                vehicle_identifiability INTEGER,
                vehicle_privacy_risk INTEGER,
                notes TEXT,
                protocol_version TEXT NOT NULL,
                annotator_id TEXT NOT NULL,
                annotation_started_at TEXT,
                annotated_at TEXT,
                annotation_duration_seconds REAL,
                is_repeat_annotation INTEGER NOT NULL DEFAULT 0,
                needs_review INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
            """
        )


def load_annotations() -> pd.DataFrame:
    with connect_database() as connection:
        return pd.read_sql_query(
            "SELECT * FROM annotations",
            connection,
        )


def load_annotation(
    annotation_queue_id: str,
) -> dict[str, Any] | None:
    with connect_database() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM annotations
            WHERE annotation_queue_id = ?
            """,
            (annotation_queue_id,),
        ).fetchone()

    return dict(row) if row else None


def upsert_annotation(record: dict[str, Any]) -> None:
    columns = [
        "annotation_queue_id",
        "annotation_status",
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
        "protocol_version",
        "annotator_id",
        "annotation_started_at",
        "annotated_at",
        "annotation_duration_seconds",
        "is_repeat_annotation",
        "needs_review",
        "updated_at",
    ]

    placeholders = ", ".join("?" for _ in columns)
    update_clause = ", ".join(
        f"{column} = excluded.{column}"
        for column in columns
        if column != "annotation_queue_id"
    )

    values = [
        record.get(column)
        for column in columns
    ]

    with connect_database() as connection:
        connection.execute(
            f"""
            INSERT INTO annotations (
                {", ".join(columns)}
            )
            VALUES ({placeholders})
            ON CONFLICT(annotation_queue_id)
            DO UPDATE SET {update_clause}
            """,
            values,
        )

    export_annotations()


def export_annotations() -> None:
    annotations = load_annotations().sort_values(
        ["annotation_queue_id"],
        kind="stable",
    )

    temporary_path = EXPORT_PATH.with_suffix(".tmp.csv")
    annotations.to_csv(
        temporary_path,
        index=False,
    )
    os.replace(
        temporary_path,
        EXPORT_PATH,
    )


# ---------------------------------------------------------------------
# Progress and navigation
# ---------------------------------------------------------------------

def annotation_status_map(
    annotations: pd.DataFrame,
) -> dict[str, str]:
    if annotations.empty:
        return {}

    return dict(
        zip(
            annotations["annotation_queue_id"].astype(str),
            annotations["annotation_status"].astype(str),
        )
    )


def mode_queue(
    queue: pd.DataFrame,
    mode: str,
) -> pd.DataFrame:
    if mode == "Pilot: first 50":
        return queue.head(PILOT_SIZE).copy()
    return queue.copy()


def first_unresolved_id(
    queue_ids: list[str],
    statuses: dict[str, str],
) -> str:
    pending = [
        queue_id
        for queue_id in queue_ids
        if statuses.get(queue_id) not in {"completed", "skipped"}
    ]
    if pending:
        return pending[0]

    skipped = [
        queue_id
        for queue_id in queue_ids
        if statuses.get(queue_id) == "skipped"
    ]
    if skipped:
        return skipped[0]

    return queue_ids[0]


def next_unresolved_id(
    queue_ids: list[str],
    statuses: dict[str, str],
    current_id: str,
) -> str:
    current_index = queue_ids.index(current_id)
    ordered_ids = (
        queue_ids[current_index + 1 :]
        + queue_ids[: current_index + 1]
    )

    for desired_status in ("pending", "skipped"):
        for queue_id in ordered_ids:
            status = statuses.get(queue_id)
            if desired_status == "pending":
                if status not in {"completed", "skipped"}:
                    return queue_id
            elif status == "skipped":
                return queue_id

    return current_id


def move_sequentially(
    queue_ids: list[str],
    current_id: str,
    offset: int,
) -> str:
    current_index = queue_ids.index(current_id)
    new_index = max(
        0,
        min(
            len(queue_ids) - 1,
            current_index + offset,
        ),
    )
    return queue_ids[new_index]


def set_current_id(
    queue_id: str,
) -> None:
    st.session_state.current_queue_id = queue_id
    st.session_state.annotation_started_at = iso_timestamp()


# ---------------------------------------------------------------------
# Validation and derived review flag
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
            errors.append(
                "Select whether a child or vulnerable person is visible."
            )
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


# ---------------------------------------------------------------------
# Streamlit page
# ---------------------------------------------------------------------

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🔎",
    layout="wide",
)

st.title(APP_TITLE)
st.caption(
    "Blinded image-level annotation for human, animal, and vehicle detection."
)

if not QUEUE_PATH.exists():
    st.error(
        "Annotation queue not found at:\n\n"
        f"`{QUEUE_PATH}`"
    )
    st.stop()

try:
    queue = load_queue(str(QUEUE_PATH))
except Exception as error:
    st.exception(error)
    st.stop()

initialise_database()
annotations = load_annotations()
statuses = annotation_status_map(annotations)

with st.sidebar:
    st.header("Session")

    mode = st.radio(
        "Annotation mode",
        options=[
            "Pilot: first 50",
            "Full dataset",
        ],
        index=0,
        help=(
            "Complete the 50-image pilot first. "
            "Switch to Full dataset after reviewing the pilot."
        ),
    )

    annotator_id = st.text_input(
        "Annotator ID",
        value="primary_annotator",
    ).strip()

    st.caption(f"Protocol version: {PROTOCOL_VERSION}")

    selected_protocol_path = protocol_path()
    if selected_protocol_path:
        with st.expander("Open annotation protocol"):
            st.markdown(
                selected_protocol_path.read_text(
                    encoding="utf-8"
                )
            )
    else:
        st.warning(
            "Protocol Markdown file was not found beside the app."
        )

active_queue = mode_queue(queue, mode)
active_ids = active_queue["annotation_queue_id"].astype(str).tolist()

if not active_ids:
    st.error("The selected queue is empty.")
    st.stop()

if (
    st.session_state.get("active_mode") != mode
    or st.session_state.get("current_queue_id") not in active_ids
):
    st.session_state.active_mode = mode
    set_current_id(
        first_unresolved_id(
            active_ids,
            statuses,
        )
    )

current_id = str(st.session_state.current_queue_id)
current_position = active_ids.index(current_id)
current_row = active_queue.iloc[current_position]
existing = load_annotation(current_id)

completed_count = sum(
    statuses.get(queue_id) == "completed"
    for queue_id in active_ids
)
skipped_count = sum(
    statuses.get(queue_id) == "skipped"
    for queue_id in active_ids
)
pending_count = (
    len(active_ids)
    - completed_count
    - skipped_count
)

active_annotation_rows = (
    annotations.loc[
        annotations["annotation_queue_id"]
        .astype(str)
        .isin(active_ids)
    ]
    if not annotations.empty
    else annotations
)

review_count = (
    int(active_annotation_rows["needs_review"].fillna(0).sum())
    if not active_annotation_rows.empty
    else 0
)

metric_columns = st.columns(5)
metric_columns[0].metric(
    "Completed",
    f"{completed_count:,}",
)
metric_columns[1].metric(
    "Pending",
    f"{pending_count:,}",
)
metric_columns[2].metric(
    "Skipped",
    f"{skipped_count:,}",
)
metric_columns[3].metric(
    "Needs review",
    f"{review_count:,}",
)
metric_columns[4].metric(
    "Current",
    f"{current_position + 1:,} / {len(active_ids):,}",
)

st.progress(
    completed_count / len(active_ids),
    text=(
        f"{completed_count:,} of {len(active_ids):,} "
        "images completed"
    ),
)

navigation_columns = st.columns(
    [1, 1, 1.4, 2.2]
)

if navigation_columns[0].button(
    "← Previous",
    width="stretch",
):
    set_current_id(
        move_sequentially(
            active_ids,
            current_id,
            -1,
        )
    )
    st.rerun()

if navigation_columns[1].button(
    "Next →",
    width="stretch",
):
    set_current_id(
        move_sequentially(
            active_ids,
            current_id,
            1,
        )
    )
    st.rerun()

if navigation_columns[2].button(
    "Next unresolved",
    width="stretch",
):
    set_current_id(
        next_unresolved_id(
            active_ids,
            statuses,
            current_id,
        )
    )
    st.rerun()

jump_id = navigation_columns[3].selectbox(
    "Jump to annotation ID",
    options=active_ids,
    index=current_position,
    label_visibility="collapsed",
)

if jump_id != current_id:
    set_current_id(str(jump_id))
    st.rerun()

current_status = (
    existing.get("annotation_status")
    if existing
    else "pending"
)

st.subheader(
    f"{current_id} · {current_status.title()}"
)

image_url = str(current_row["annotation_image_url"])

try:
    st.image(
        image_url,
        width="stretch",
    )
except Exception as error:
    st.error(
        "The image could not be displayed in the app."
    )
    st.exception(error)

st.markdown(
    f"[Open the full-resolution image in a new tab]({image_url})"
)

with st.expander(
    "Image identifiers",
    expanded=False,
):
    identifier_columns = [
        column
        for column in [
            "annotation_queue_id",
            "photo_id",
            "sequence_id",
            "site_id",
            "filename",
        ]
        if column in current_row.index
    ]

    st.dataframe(
        pd.DataFrame(
            {
                "field": identifier_columns,
                "value": [
                    current_row[column]
                    for column in identifier_columns
                ],
            }
        ),
        hide_index=True,
        width="stretch",
    )

existing_human = (
    existing.get("manual_human_present")
    if existing
    else None
)
existing_animal = (
    existing.get("manual_animal_present")
    if existing
    else None
)
existing_vehicle = (
    existing.get("manual_vehicle_present")
    if existing
    else None
)
existing_quality = (
    existing.get("annotation_quality")
    if existing
    else None
)

with st.form(
    key=f"annotation_form_{current_id}",
    clear_on_submit=False,
    enter_to_submit=False,
):
    st.subheader("Core labels")

    core_columns = st.columns(4)

    quality = core_columns[0].selectbox(
        "Image quality",
        options=QUALITY_OPTIONS,
        index=option_index(
            QUALITY_OPTIONS,
            existing_quality,
        ),
    )

    human = core_columns[1].selectbox(
        "Human present",
        options=PRESENCE_OPTIONS,
        index=option_index(
            PRESENCE_OPTIONS,
            existing_human,
        ),
    )

    animal = core_columns[2].selectbox(
        "Animal present",
        options=PRESENCE_OPTIONS,
        index=option_index(
            PRESENCE_OPTIONS,
            existing_animal,
        ),
    )

    vehicle = core_columns[3].selectbox(
        "Vehicle present",
        options=PRESENCE_OPTIONS,
        index=option_index(
            PRESENCE_OPTIONS,
            existing_vehicle,
        ),
    )

    st.caption(
        "When Image quality is Unusable, all three presence labels "
        "will be saved as Uncertain."
    )

    with st.expander(
        "Human-specific labels — complete only when Human = Yes",
        expanded=human == "Yes",
    ):
        human_columns = st.columns(4)

        human_recognisability_label = (
            human_columns[0].selectbox(
                "Human recognisability",
                options=HUMAN_RECOGNISABILITY_OPTIONS,
                index=option_index(
                    HUMAN_RECOGNISABILITY_OPTIONS,
                    score_label(
                        existing.get(
                            "human_recognisability"
                        )
                        if existing
                        else None,
                        HUMAN_RECOGNISABILITY_OPTIONS,
                    ),
                ),
            )
        )

        child_vulnerable = human_columns[1].selectbox(
            "Child/vulnerable person visible",
            options=CHILD_VULNERABLE_OPTIONS,
            index=option_index(
                CHILD_VULNERABLE_OPTIONS,
                (
                    existing.get(
                        "child_or_vulnerable_person_visible"
                    )
                    if existing
                    else None
                ),
            ),
        )

        human_privacy_label = (
            human_columns[2].selectbox(
                "Human privacy risk",
                options=HUMAN_PRIVACY_OPTIONS,
                index=option_index(
                    HUMAN_PRIVACY_OPTIONS,
                    score_label(
                        existing.get(
                            "human_privacy_risk"
                        )
                        if existing
                        else None,
                        HUMAN_PRIVACY_OPTIONS,
                    ),
                ),
            )
        )

        safeguarding_label = (
            human_columns[3].selectbox(
                "Safeguarding risk",
                options=SAFEGUARDING_OPTIONS,
                index=option_index(
                    SAFEGUARDING_OPTIONS,
                    score_label(
                        existing.get(
                            "safeguarding_risk"
                        )
                        if existing
                        else None,
                        SAFEGUARDING_OPTIONS,
                    ),
                ),
            )
        )

        st.caption(
            "A child or vulnerable person can be visible while "
            "safeguarding risk remains 0."
        )

    with st.expander(
        "Vehicle-specific labels — complete only when Vehicle = Yes",
        expanded=vehicle == "Yes",
    ):
        vehicle_columns = st.columns(2)

        vehicle_identifiability_label = (
            vehicle_columns[0].selectbox(
                "Vehicle identifiability",
                options=VEHICLE_IDENTIFIABILITY_OPTIONS,
                index=option_index(
                    VEHICLE_IDENTIFIABILITY_OPTIONS,
                    score_label(
                        existing.get(
                            "vehicle_identifiability"
                        )
                        if existing
                        else None,
                        VEHICLE_IDENTIFIABILITY_OPTIONS,
                    ),
                ),
            )
        )

        vehicle_privacy_label = (
            vehicle_columns[1].selectbox(
                "Vehicle privacy risk",
                options=VEHICLE_PRIVACY_OPTIONS,
                index=option_index(
                    VEHICLE_PRIVACY_OPTIONS,
                    score_label(
                        existing.get(
                            "vehicle_privacy_risk"
                        )
                        if existing
                        else None,
                        VEHICLE_PRIVACY_OPTIONS,
                    ),
                ),
            )
        )

        st.caption(
            "A readable plate on an ordinary public road is usually "
            "identifiability 2 and privacy risk 1."
        )

    notes = st.text_area(
        "Notes — optional",
        value=(
            existing.get("notes") or ""
            if existing
            else ""
        ),
        height=90,
        placeholder=(
            "Use only for unusual or ambiguous decisions."
        ),
    )

    save_submitted = st.form_submit_button(
        "Save and next",
        type="primary",
        width="stretch",
    )

action_columns = st.columns(2)

skip_clicked = action_columns[0].button(
    "Skip for later",
    width="stretch",
    disabled=current_status == "completed",
)

export_clicked = action_columns[1].button(
    "Export annotations to CSV",
    width="stretch",
)

if export_clicked:
    export_annotations()
    st.success(
        f"Exported annotations to `{EXPORT_PATH}`."
    )

if skip_clicked:
    if not annotator_id:
        st.error("Enter an Annotator ID before continuing.")
    else:
        started_at_text = st.session_state.get(
            "annotation_started_at",
            iso_timestamp(),
        )
        started_at = datetime.fromisoformat(
            started_at_text
        )
        finished_at = utc_now()

        upsert_annotation(
            {
                "annotation_queue_id": current_id,
                "annotation_status": "skipped",
                "manual_human_present": None,
                "manual_animal_present": None,
                "manual_vehicle_present": None,
                "annotation_quality": None,
                "human_recognisability": None,
                "child_or_vulnerable_person_visible": None,
                "human_privacy_risk": None,
                "safeguarding_risk": None,
                "vehicle_identifiability": None,
                "vehicle_privacy_risk": None,
                "notes": None,
                "protocol_version": PROTOCOL_VERSION,
                "annotator_id": annotator_id,
                "annotation_started_at": started_at_text,
                "annotated_at": iso_timestamp(finished_at),
                "annotation_duration_seconds": round(
                    (
                        finished_at
                        - started_at
                    ).total_seconds(),
                    2,
                ),
                "is_repeat_annotation": 0,
                "needs_review": 0,
                "updated_at": iso_timestamp(finished_at),
            }
        )

        refreshed_statuses = annotation_status_map(
            load_annotations()
        )
        set_current_id(
            next_unresolved_id(
                active_ids,
                refreshed_statuses,
                current_id,
            )
        )
        st.rerun()

if save_submitted:
    if not annotator_id:
        st.error("Enter an Annotator ID before saving.")
        st.stop()

    errors = validate_form(
        quality=quality,
        human=human,
        animal=animal,
        vehicle=vehicle,
        human_recognisability_label=(
            human_recognisability_label
        ),
        child_vulnerable=child_vulnerable,
        human_privacy_label=human_privacy_label,
        safeguarding_label=safeguarding_label,
        vehicle_identifiability_label=(
            vehicle_identifiability_label
        ),
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
        human_recognisability = numeric_score(
            human_recognisability_label
        )
        child_vulnerable_value = child_vulnerable
        human_privacy = numeric_score(
            human_privacy_label
        )
        safeguarding = numeric_score(
            safeguarding_label
        )
    else:
        human_recognisability = None
        child_vulnerable_value = None
        human_privacy = None
        safeguarding = None

    if vehicle == "Yes":
        vehicle_identifiability = numeric_score(
            vehicle_identifiability_label
        )
        vehicle_privacy = numeric_score(
            vehicle_privacy_label
        )
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

    started_at_text = st.session_state.get(
        "annotation_started_at",
        iso_timestamp(),
    )
    started_at = datetime.fromisoformat(
        started_at_text
    )
    finished_at = utc_now()

    upsert_annotation(
        {
            "annotation_queue_id": current_id,
            "annotation_status": "completed",
            "manual_human_present": human,
            "manual_animal_present": animal,
            "manual_vehicle_present": vehicle,
            "annotation_quality": quality,
            "human_recognisability": (
                human_recognisability
            ),
            "child_or_vulnerable_person_visible": (
                child_vulnerable_value
            ),
            "human_privacy_risk": human_privacy,
            "safeguarding_risk": safeguarding,
            "vehicle_identifiability": (
                vehicle_identifiability
            ),
            "vehicle_privacy_risk": vehicle_privacy,
            "notes": safe_text(notes),
            "protocol_version": PROTOCOL_VERSION,
            "annotator_id": annotator_id,
            "annotation_started_at": started_at_text,
            "annotated_at": iso_timestamp(finished_at),
            "annotation_duration_seconds": round(
                (
                    finished_at
                    - started_at
                ).total_seconds(),
                2,
            ),
            "is_repeat_annotation": 0,
            "needs_review": int(needs_review),
            "updated_at": iso_timestamp(finished_at),
        }
    )

    refreshed_statuses = annotation_status_map(
        load_annotations()
    )
    set_current_id(
        next_unresolved_id(
            active_ids,
            refreshed_statuses,
            current_id,
        )
    )
    st.rerun()

if mode == "Pilot: first 50" and completed_count == len(active_ids):
    st.success(
        "The 50-image pilot is complete. Review it before "
        "switching to Full dataset mode."
    )
