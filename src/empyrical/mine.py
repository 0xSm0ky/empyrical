import json

from .core import get_freq_list, prepare


def find_1t_sentences(processed, known, max_results=None):
    """Yield `(unknown_lemma, sentence_lemmas)` for each sentence with exactly one unknown lemma.

    `known` is a set of lemmas the learner already knows.
    Stops once `max_results` matches are collected (None = unbounded).
    """
    known_set = set(known)
    out = []
    for sentence in processed:
        unknown = [w for w in set(sentence) if w not in known_set]
        if len(unknown) == 1:
            out.append((unknown[0], sentence))
            if max_results is not None and len(out) >= max_results:
                break
    return out


def _load_known_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def _write_jsonl(path, results):
    with open(path, "w", encoding="utf-8") as f:
        for unknown, sentence in results:
            f.write(json.dumps({"unknown": unknown, "sentence": sentence}) + "\n")


def run(args):
    processed = prepare(args)
    if args.known:
        known = _load_known_from_file(args.known)
    else:
        word_freqs = get_freq_list(processed)
        known = {w for w, _ in word_freqs[: args.top_n]}
    results = find_1t_sentences(processed, known, max_results=args.max)
    if args.out_jsonl:
        _write_jsonl(args.out_jsonl, results)
    else:
        for unknown, sentence in results:
            print(f"[{unknown}]  {' '.join(sentence)}")
    print(f"\nFound {len(results)} 1T sentences (known set size: {len(known)}).")
