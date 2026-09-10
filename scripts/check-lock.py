"""Check installed versions against recursively included requirement locks."""
import argparse
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def collect(path: Path, expected: dict[str, str], visited: set[Path]) -> None:
    path = path.resolve()
    if path in visited:
        return
    visited.add(path)
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r "):
            collect(path.parent / line[3:].strip(), expected, visited)
            continue
        name, pin = line.split("==", 1)
        name = name.lower().replace("_", "-")
        if name in expected and expected[name] != pin:
            raise ValueError(f"Conflicting pins for {name}")
        expected[name] = pin


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-only", action="store_true")
    args = parser.parse_args()
    expected = {}
    name = "requirements.lock.txt" if args.runtime_only else "requirements-dev.lock.txt"
    collect(ROOT / "backend" / name, expected, set())
    failures = []
    for package, pin in sorted(expected.items()):
        try:
            actual = version(package)
        except PackageNotFoundError:
            actual = "missing"
        if actual != pin:
            failures.append(f"{package}: expected {pin}, found {actual}")
    if failures:
        print("\n".join(failures))
        print("Run scripts/setup.ps1 to install the locked environment.")
        return 1
    print(f"Dependency lock verified: {len(expected)} packages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
