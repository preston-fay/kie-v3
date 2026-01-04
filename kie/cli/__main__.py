"""
CLI entry point for KIE.

Usage:
    python -m kie.cli init
    python -m kie.cli doctor
"""

from kie.cli.workspace import main

if __name__ == '__main__':
    main()
