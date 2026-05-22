"""Extract known-word lists from Anki `.apkg` exports."""
import json
import re
import sqlite3
import tempfile
import zipfile
from pathlib import Path

try:
    import zstandard as zstd
except ImportError:
    zstd = None


_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SOUND_RE = re.compile(r"\[sound:[^\]]*\]")
_IMG_RE = re.compile(r"\[image:[^\]]*\]")
# Zero-width spaces (U+200B-200F), BIDI markers (U+202A-202E), BOM (U+FEFF) — copy-paste noise.
_INVIS_RE = re.compile("[​-‏‪-‮﻿]")


# Anki card.type:  0=new, 1=learning, 2=review, 3=relearning
# Anki card.queue: -3=user-buried, -2=sched-buried, -1=suspended,
#                   0=new, 1=learning, 2=review, 3=day-learning, 4=preview
STATUS_FILTERS = {
    "mature":   "type = 2 AND queue != -1 AND ivl >= 21",
    "young":    "type = 2 AND queue != -1 AND ivl >= 7",
    "review":   "type = 2 AND queue != -1",
    "learning": "type IN (1, 2, 3) AND queue != -1",
    "all":      "1=1",
}


def _clean_field(value):
    if not value:
        return ""
    value = _SOUND_RE.sub("", value)
    value = _IMG_RE.sub("", value)
    value = _HTML_TAG_RE.sub("", value)
    value = _INVIS_RE.sub("", value)
    value = value.replace("\xa0", " ")
    return value.strip()


def _open_collection(apkg_path):
    """Decompress the Anki collection and return `(sqlite3.Connection, tempdir)`.

    Caller is responsible for closing the connection and cleaning up the tempdir.
    """
    apkg = Path(apkg_path)
    td = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(apkg) as z:
        names = z.namelist()
        db_name = next(
            (n for n in ("collection.anki21b", "collection.anki21", "collection.anki2") if n in names),
            None,
        )
        if db_name is None:
            td.cleanup()
            raise ValueError(f"{apkg}: no Anki collection database found in archive")
        raw = z.read(db_name)
    db_path = Path(td.name) / "collection.sqlite"
    if db_name.endswith("21b"):
        if zstd is None:
            td.cleanup()
            raise RuntimeError(
                "Anki 21b deck requires the `zstandard` package. Install with `pip install zstandard`."
            )
        db_path.write_bytes(zstd.ZstdDecompressor().decompress(raw, max_output_size=512 * 1024 * 1024))
    else:
        db_path.write_bytes(raw)
    con = sqlite3.connect(db_path)
    # Anki defines a custom collation that stock sqlite doesn't know; a case-fold compare
    # is sufficient since none of our queries filter on collated columns.
    con.create_collation(
        "unicase",
        lambda a, b: (a.casefold() > b.casefold()) - (a.casefold() < b.casefold()),
    )
    return con, td


def _resolve_field_ord(con, field_name):
    """Map note-type-id -> field ord for the given field name across all note types."""
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}
    if "notetypes" in tables and "fields" in tables:
        cur.execute("SELECT ntid, ord FROM fields WHERE name = ?", (field_name,))
        return dict(cur.fetchall())
    # Legacy: models JSON in col table
    cur.execute("SELECT models FROM col")
    row = cur.fetchone()
    if not row or not row[0]:
        return {}
    models = json.loads(row[0])
    out = {}
    for mid, m in models.items():
        for f in m.get("flds", []):
            if f["name"] == field_name:
                out[int(mid)] = f["ord"]
                break
    return out


def extract_known_words(apkg_path, *, status="mature", field="Word"):
    """Return the set of words you "know" in this deck.

    Args:
        apkg_path: path to an Anki `.apkg` (with scheduling info included).
        status: which cards count as known. One of:
            mature   - review cards with interval >= 21d (Anki's mature definition)
            young    - review cards with interval >= 7d
            review   - any review card (interval >= 1d, graduated)
            learning - any card currently being studied (excludes new)
            all      - every card in the deck
            Suspended cards are always excluded (except for `all`).
        field: name of the note field holding the target word.
    """
    if status not in STATUS_FILTERS:
        raise ValueError(f"Unknown status {status!r}. Pick one of: {sorted(STATUS_FILTERS)}")
    con, td = _open_collection(apkg_path)
    try:
        cur = con.cursor()
        field_map = _resolve_field_ord(con, field)
        if not field_map:
            raise ValueError(f"Field {field!r} not found in any note type in this deck.")
        where = STATUS_FILTERS[status]
        cur.execute(f"SELECT DISTINCT nid FROM cards WHERE {where}")
        nids = [r[0] for r in cur.fetchall()]
        if not nids:
            return set()
        words = set()
        # Chunk in case the deck has more notes than SQLite's host-parameter limit.
        CHUNK = 500
        for i in range(0, len(nids), CHUNK):
            chunk = nids[i : i + CHUNK]
            placeholders = ",".join("?" * len(chunk))
            cur.execute(f"SELECT mid, flds FROM notes WHERE id IN ({placeholders})", chunk)
            for mid, flds in cur.fetchall():
                ord_ = field_map.get(mid)
                if ord_ is None:
                    continue
                parts = flds.split("\x1f")
                if ord_ < len(parts):
                    w = _clean_field(parts[ord_])
                    if w:
                        words.add(w)
        return words
    finally:
        con.close()
        try:
            td.cleanup()
        except PermissionError:
            # Windows occasionally holds the file briefly after close; safe to leave.
            pass


def write_known_file(apkg_path, out_path, *, status="mature", field="Word"):
    """Extract and write one word per line (UTF-8, sorted) to `out_path`."""
    words = extract_known_words(apkg_path, status=status, field=field)
    sorted_words = sorted(words)
    Path(out_path).write_text("\n".join(sorted_words) + "\n", encoding="utf-8")
    return sorted_words


def run(args):
    words = write_known_file(
        args.apkg, args.out, status=args.status, field=args.field
    )
    print(f"Wrote {len(words)} known words (status={args.status}, field={args.field!r}) to {args.out}")
