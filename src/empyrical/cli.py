import argparse
import sys

from . import __version__
from . import hill1t as _hill1t
from . import coverage as _coverage
from . import mine as _mine
from . import anki as _anki


def _add_shared(p):
    p.add_argument(
        "text_path",
        nargs="?",
        default=None,
        help="Directory of .txt files to analyze. Required unless --parsed is given.",
    )
    p.add_argument(
        "--spacy-pipeline",
        default="en_core_web_sm",
        help="spaCy pipeline name. See https://spacy.io/models/",
    )
    p.add_argument(
        "--parsed",
        default=None,
        help="Path to a JSON cache of pre-lemmatized sentences. Skips spaCy entirely.",
    )
    p.add_argument(
        "--save-parsed",
        dest="save_parsed",
        default=None,
        help="If set, save the lemmatized output to this path for reuse.",
    )


def _add_plot_outputs(p):
    p.add_argument("--out-csv", dest="out_csv", default=None, help="Write data rows to this CSV path.")
    p.add_argument("--out-png", dest="out_png", default=None, help="Save the plot to this PNG path (skips the interactive window).")


def _validate_inputs(args):
    # Subcommands that don't take corpus input (e.g. anki-import) opt out.
    if not getattr(args, "validate_inputs", True):
        return
    if not args.parsed and not args.text_path:
        sys.exit("error: either text_path or --parsed must be provided")


def build_parser():
    parser = argparse.ArgumentParser(prog="empyrical", description="Empirical analyses for immersion language learning.")
    parser.add_argument("--version", action="version", version=f"empyrical {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_hill = sub.add_parser("hill1t", help="1T-sentence hill: count one-unknown sentences per step of learning.")
    _add_shared(p_hill)
    _add_plot_outputs(p_hill)
    p_hill.set_defaults(func=_hill1t.run)

    p_cov = sub.add_parser("coverage", help="Cumulative token coverage by top-N most frequent lemmas.")
    _add_shared(p_cov)
    _add_plot_outputs(p_cov)
    p_cov.set_defaults(func=_coverage.run)

    p_mine = sub.add_parser("mine", help="Extract actual 1T sentences given a known-word set.")
    _add_shared(p_mine)
    group = p_mine.add_mutually_exclusive_group()
    group.add_argument("--known", default=None, help="Path to a newline-separated file of known lemmas.")
    group.add_argument("--top-n", dest="top_n", type=int, default=1000, help="Treat the top-N most frequent lemmas as known (default 1000). Ignored if --known is set.")
    p_mine.add_argument("--max", dest="max", type=int, default=None, help="Stop after this many matches.")
    p_mine.add_argument("--out-jsonl", dest="out_jsonl", default=None, help="Write matches as JSONL instead of printing.")
    p_mine.set_defaults(func=_mine.run)

    p_anki = sub.add_parser("anki-import", help="Extract a known-word list from an Anki .apkg deck.")
    p_anki.add_argument("apkg", help="Path to the .apkg file (must include scheduling info).")
    p_anki.add_argument("-o", "--out", required=True, help="Output path for the known-words list (one per line).")
    p_anki.add_argument(
        "--status",
        default="mature",
        choices=sorted(_anki.STATUS_FILTERS),
        help="Which cards count as known. Default: mature (review cards with interval >= 21d).",
    )
    p_anki.add_argument(
        "--field",
        default="Word",
        help="Name of the note field holding the target word (default: Word).",
    )
    p_anki.set_defaults(func=_anki.run, validate_inputs=False)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    _validate_inputs(args)
    args.func(args)


if __name__ == "__main__":
    main()
