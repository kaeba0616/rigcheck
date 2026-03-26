"""RigCheck CLI."""
import sys
from .engine import run_check


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m rigcheck <runtime_directory>")
        print("Example: python -m rigcheck ./ren_pro_ko/runtime")
        sys.exit(1)

    runtime_dir = sys.argv[1]
    try:
        report = run_check(runtime_dir)
        print(report.summary())
        sys.exit(1 if report.critical_count > 0 else 0)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
