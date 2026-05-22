import json
import os
import re
from collections import Counter

from tqdm import tqdm


def find_text_files(directory):
    files = []
    for subdir, _, fs in tqdm(os.walk(os.path.abspath(directory)), desc="Scanning for Text"):
        for f in fs:
            if f.endswith(".txt"):
                files.append(os.path.join(subdir, f))
    return files


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


def compile_texts(files):
    texts = []
    for path in tqdm(files, desc="Reading Raw Text"):
        texts.append(_read_text(path))
    return [re.sub(r"\s+", " ", t.strip()) for t in texts]


def _sentences(spacy_model, texts):
    out = []
    for text in tqdm(texts, desc="Parsing Text"):
        out += spacy_model(text).sents
    return out


_DROP_POS = {"PUNCT", "SPACE", "PROPN"}


def lemmatize(spacy_model, texts):
    """Run spaCy over `texts` and return per-sentence lemma lists.

    Drops PUNCT, SPACE, and PROPN tokens. Empty sentences are filtered out.
    """
    sentences = _sentences(spacy_model, texts)
    processed = []
    for sent in tqdm(sentences, desc="Extracting Lemmas"):
        lemmas = [tok.lemma_ for tok in sent if tok.pos_ not in _DROP_POS]
        if lemmas:
            processed.append(lemmas)
    return processed


def get_freq_list(processed):
    """Return `[(lemma, count), ...]` sorted by count descending, then lemma ascending for stable ties."""
    counts = Counter(w for s in processed for w in s)
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))


def load_cache(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or (data and not isinstance(data[0], list)):
        raise ValueError(f"{path}: expected JSON list[list[str]]")
    return data


def save_cache(path, processed):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(processed, f)


def prepare(args):
    """Resolve `args` to a processed-lemma list.

    If `args.parsed` is set, load the cache. Otherwise read text from `args.text_path`,
    run spaCy with `args.spacy_pipeline`, and optionally save the result to `args.save_parsed`.
    """
    if args.parsed:
        return load_cache(args.parsed)
    import spacy  # imported lazily so cache-only runs don't pay the spaCy import cost
    files = find_text_files(args.text_path)
    texts = compile_texts(files)
    processed = lemmatize(spacy.load(args.spacy_pipeline), texts)
    if args.save_parsed:
        save_cache(args.save_parsed, processed)
    return processed
