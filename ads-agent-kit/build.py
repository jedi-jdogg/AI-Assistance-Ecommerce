#!/usr/bin/env python3
"""Assemble the self-contained Foresite Ads Agent skills from ads-agent-kit/.

  python3 ads-agent-kit/build.py           # (re)build .claude/skills/foresite-ads-b2c and -b2b
  python3 ads-agent-kit/build.py --zip     # also write dist/foresite-ads-b2c.zip / -b2b.zip for claude.ai upload
  python3 ads-agent-kit/build.py --check   # exit 1 if the built skills are out of date (CI)

Edit sources only under ads-agent-kit/ (shared/ for both skills, b2c/ or b2b/ for one). Never hand-edit the
built copies under .claude/skills/foresite-ads-*/ — they are overwritten.
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parent
ROOT = KIT.parent
SKILLS = ROOT / ".claude" / "skills"
MODELS = ("b2c", "b2b")


def layout(model: str) -> dict[str, Path]:
    """Map relative path inside the built skill -> source file."""
    files: dict[str, Path] = {"SKILL.md": KIT / model / "SKILL.md"}
    for src in sorted((KIT / "shared" / "references").glob("*.md")):
        files[f"references/{src.name}"] = src
    files[f"references/{model}-playbook.md"] = KIT / model / f"{model}-playbook.md"
    for src in sorted((KIT / "shared" / "templates").iterdir()):
        files[f"templates/{src.name}"] = src
    files["scripts/adsctl.py"] = KIT / "shared" / "scripts" / "adsctl.py"
    return files


def dest(model: str) -> Path:
    return SKILLS / f"foresite-ads-{model}"


def build(model: str) -> None:
    out = dest(model)
    if out.exists():
        shutil.rmtree(out)
    for rel, src in layout(model).items():
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    print(f"built {out.relative_to(ROOT)} ({len(layout(model))} files)")


def check(model: str) -> list[str]:
    out = dest(model)
    want = layout(model)
    problems = []
    for rel, src in want.items():
        target = out / rel
        if not target.exists():
            problems.append(f"missing {target.relative_to(ROOT)}")
        elif not filecmp.cmp(src, target, shallow=False):
            problems.append(f"stale   {target.relative_to(ROOT)}")
    if out.exists():
        for f in out.rglob("*"):
            if f.is_file() and str(f.relative_to(out)) not in want and "__pycache__" not in f.parts:
                problems.append(f"extra   {f.relative_to(ROOT)}")
    return problems


def make_zip(model: str) -> Path:
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    zpath = dist / f"foresite-ads-{model}.zip"
    out = dest(model)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, Path(out.name) / f.relative_to(out))
    print(f"zipped {zpath.relative_to(ROOT)}")
    return zpath


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--zip", action="store_true")
    a = ap.parse_args()
    if a.check:
        problems = [p for m in MODELS for p in check(m)]
        for p in problems:
            print(p)
        if problems:
            print("Run: python3 ads-agent-kit/build.py")
            return 1
        print("foresite-ads skills are up to date")
        return 0
    for m in MODELS:
        build(m)
        if a.zip:
            make_zip(m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
