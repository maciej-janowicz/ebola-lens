"""Command-line entry point for EbolaLens."""

import argparse

from ebolalens import __version__


def main() -> None:
    """Run the EbolaLens command-line interface."""
    parser = argparse.ArgumentParser(prog="ebolalens")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.parse_args()


if __name__ == "__main__":
    main()
