import re

SUBSTITUTIONS = [
    ("ee", "i"), ("oo", "u"), ("aa", "a"),
    ("th", "t"), ("dh", "d"), ("bh", "b"),
    ("kh", "k"), ("gh", "g"), ("ph", "p"), ("sh", "s"),
    ("w", "v"), ("z", "j"),
]

AGE_TOLERANCE = 3

def normalize_name(name: str) -> str:
    """Collapse common Indic transliteration variants to one canonical form."""
    s = re.sub(r"[^a-z]","", name.lowe().strip())
    for old,new in SUBSTITUTIONS:
        s = s.replace(old,new)

    s = re.sub(r"(.)\1+", r"\1", s)
    s = re.sub(r"\s+", " ", s)
    return s

def find_candidate(conn, display_name, age , village=None):
    """Return the best existing patient row, or None if we should create a new one."""
    norm = normalize_name(display_name)
    rows = conn.execute("SELECT * FROM patients WHERE normalized_name = ?", (norm,)
).fetchall()
    

    best = None

    for row in rows:
        if village and row["village"] and village.lower() != row[village].lower():
            continue
        if age is not None and row["age"] is not None:
            if abs(row["age"] - age) > AGE_TOLERANCE:
                continue
        best = row
        break
    return best






