"""Command-line interface for the Kannada tokenizer."""

from __future__ import annotations

import argparse
import sys

from .tokenizer import tokenize, tokenize_words


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="kannada-tokenize",
        description="Tokenize Kannada text with optional sandhi splitting.",
    )
    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Kannada text to tokenize. Reads from stdin if omitted.",
    )
    parser.add_argument(
        "--no-sandhi",
        action="store_true",
        default=False,
        help="Disable sandhi splitting (word-level tokenization only).",
    )
    parser.add_argument(
        "--separator",
        "-s",
        default="\n",
        help="Token separator in output (default: newline).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``kannada-tokenize`` CLI.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Determine input source
    if args.text is not None:
        text: str = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    # Select tokenization strategy
    tok_fn = tokenize_words if args.no_sandhi else tokenize
    tokens: list[str] = tok_fn(text)

    if tokens:
        print(args.separator.join(tokens))


if __name__ == "__main__":
    main()
