import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from cli.commands import run_app
from cli.parser import parse_args


def main() -> None:
    try:
        args = parse_args()
        exit_code = run_app(args)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.stderr.write("\nOperation cancelled by user.\n")
        sys.exit(130)
    except Exception as exc:
        sys.stderr.write(f"\nFatal error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
