"""Allow ``python -m forge`` to dispatch to the CLI."""

from forge.cli import main
import sys

if __name__ == "__main__":
    sys.exit(main())
