from __future__ import annotations

import argparse
from pathlib import Path

from validation import validate_agent


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an agent.py submission")
    parser.add_argument("agent", nargs="?", default="agent.py")
    agent_path = Path(parser.parse_args().agent).resolve()
    errors = validate_agent(agent_path)
    if errors:
        print("INVALID agent.py")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID agent.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
