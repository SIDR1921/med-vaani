import json
import logging
import re

import ollama

import config

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """Extract the patient's data from this field report segment.

Segment:
\"\"\"{segment}\"\"\"

Return ONLY this JSON. For EVERY field, give the value AND the exact quote
(copied verbatim from the segment) that contains it. If the segment does not
state a field, use null for both value and quote. NEVER guess.

{{
  "patient_name": {{"value": "string or null", "quote": "string or null"}},
  "age":          {{"value": "integer or null", "quote": "string or null"}},
  "systolic_bp":  {{"value": "integer or null", "quote": "string or null"}},
  "diastolic_bp": {{"value": "integer or null", "quote": "string or null"}},
  "symptoms":     {{"value": "string or null", "quote": "string or null"}},
  "village":      {{"value": "string or null", "quote": "string or null"}}
}}
"""

_NUMERIC_FIELDS = ("age", "systolic_bp", "diastolic_bp")
_TEXT_FIELDS = ("patient_name", "symptoms", "village")


def _norm(text: str) -> str:
    """Normalise for containment checks: lowercase, collapse whitespace."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def _quote_in_segment(quote: str, segment: str) -> bool:
    return bool(quote) and _norm(quote) in _norm(segment)


def _verified_numeric(field, payload, segment):
    value, quote = payload.get("value"), payload.get("quote")
    if value is None:
        return None
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    if not _quote_in_segment(quote or "", segment):
        logger.warning("Dropped %s=%s: quote not found in segment", field, value)
        return None
    if str(value) not in quote:
        logger.warning("Dropped %s=%s: number not present in its own quote", field, value)
        return None
    low, high = config.VALID_RANGES[field]
    if not (low <= value <= high):
        logger.warning("Dropped %s=%s: outside plausible range %s-%s", field, value, low, high)
        return None
    return value


def _verified_text(field, payload, segment):
    value, quote = payload.get("value"), payload.get("quote")
    if not value or not isinstance(value, str):
        return None
    if not _quote_in_segment(quote or "", segment):
        logger.warning("Dropped %s=%r: quote not found in segment", field, value)
        return None
    return value.strip()


def extract_patient(segment: str) -> dict | None:
    try:
        response = ollama.chat(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": EXTRACT_PROMPT.format(segment=segment)}],
            format="json",
        )
        raw = json.loads(response["message"]["content"])
    except Exception as exc:
        logger.error("Extraction failed: %s", exc)
        return None

    record = {}
    for field in _NUMERIC_FIELDS:
        record[field] = _verified_numeric(field, raw.get(field) or {}, segment)
    for field in _TEXT_FIELDS:
        record[field] = _verified_text(field, raw.get(field) or {}, segment)

    if not record["patient_name"]:
        return None  # a record with no verifiable name is not a record

    record["source_excerpt"] = segment[:500]
    return record