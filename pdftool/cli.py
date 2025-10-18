"""Command-line interface for PDF to Markdown conversion using Azure Document Intelligence."""
import os
import sys
import argparse

from pdftool.processing.extract import extract_pdf_to_markdown


def cli():
    """Main CLI entry point for PDF to Markdown conversion."""
    parser = argparse.ArgumentParser(
        prog="pdftool",
        description="PDF -> Markdown (Azure OCR) converter"
    )
    sub = parser.add_subparsers(dest="command")

    p_convert = sub.add_parser(
        "convert",
        help="Convert a PDF to Markdown using Azure Document Intelligence"
    )
    p_convert.add_argument("pdf", help="Path to the input PDF file")
    p_convert.add_argument("-o", "--output", help="Output Markdown file path")
    p_convert.add_argument(
        "--dpi",
        type=int,
        default=0,
        help="Override OCR render DPI (default: 1200)"
    )
    p_convert.add_argument(
        "--start",
        type=int,
        help="Start page (1-based, inclusive)"
    )
    p_convert.add_argument(
        "--end",
        type=int,
        help="End page (1-based, inclusive)"
    )
    p_convert.add_argument(
        "--keep-png",
        action="store_true",
        help="Retain rendered page PNGs (saved next to output)"
    )

    args = parser.parse_args()

    if args.command == "convert":
        pdf_path = os.path.abspath(args.pdf)
        if not os.path.exists(pdf_path):
            print(f"Error: file not found: {pdf_path}", file=sys.stderr)
            sys.exit(1)
        if not pdf_path.lower().endswith(".pdf"):
            print("Error: input must be a .pdf file", file=sys.stderr)
            sys.exit(1)

        outputs_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(outputs_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        out_md = (
            os.path.abspath(args.output)
            if args.output
            else os.path.join(outputs_dir, f"{base}.md")
        )

        print(f"Converting\n  PDF: {pdf_path}\n  Out: {out_md}")
        try:
            extract_pdf_to_markdown(
                pdf_path,
                out_md,
                dpi=(args.dpi if args.dpi > 0 else None),
                start_page=args.start,
                end_page=args.end,
                keep_png=args.keep_png,
            )
        except (ValueError, RuntimeError, OSError) as e:
            print(f"Extraction failed: {e}", file=sys.stderr)
            sys.exit(2)
        print(f"Done -> {out_md}")
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    cli()
