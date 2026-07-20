import json
import logging
import re
import ollama
import config

logger - logging.getLogger(__name__)
SEGMENT_PROMPT = """You are given a transcript in which a community health worker
describes one or more patients, possibly in Hindi, English, or a mix.

Split the transcript into one segment per patient.

Rules:
- Copy the words EXACTLY as written. Do not translate, paraphrase, or summarise.
- Every sentence about a patient appears in exactly one segment.
- Ignore greetings or chatter that is about no patient.

Return ONLY this JSON:
{{"segments": ["<text for patient 1>", "<text for patient 2>"]}}

Transcript:
\"\"\"{transcript}\"\"\"
"""

def segment_transcript(transcript:str) -> list[str]:
    try:
        response = ollama.chat(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": SEGMENT_PROMPT.format(transcript=transcript)}],
            format="json",
        )
        data = json.loads(response["message"]["content"])
        segments = [s.strip() for s in data.get("segments", []) if len(s.strip()) > 10]

        if segments:
            return segments
        logger.warning("LLM returned no usable segments; falling back to regex")
    except Exception as exc:
        logger.warning("Segmentation LLM failed (%s); falling back to regex", exc)
    return regex_fallback(transcript)

def regex_fallback(transcript:str) -> list[str]:
    parts = re.split(r"(?i)(?=\b(?:first|second|third|fourth|fifth|next|another|"
        r"pehla|doosra|dusra|teesra|agla)\b)",
        transcript,
)
    parts = [p.strip() for p in parts if len(p.strip()) > 10]
    return parts or [transcript]

