import json
import re
from pathlib import Path


ROOT = Path(r"D:\Projects\TilesSurvive")
HTML_PATH = ROOT / "Index.html"
BP_PATH = ROOT / "research" / "battle_power_tables.json"
REPORT_PATH = ROOT / "cx_update_team_builder_report.txt"

BP_PATTERN = re.compile(
    r"    const BP = .*?;\n\n"
    r"    // ═══════════════════════════════════════════════════\n"
    r"    // HEROES DATABASE",
    re.DOTALL,
)

CONTROLS = {
    "becca": {
        "level": 130,
        "rank": 3,
        "skills": {"attack": 1, "skill_1": 1, "skill_2": 5, "skill_3": 0},
        "expected": 534042,
    },
    "tara": {
        "level": 130,
        "rank": 2,
        "skills": {"attack": 1, "skill_1": 1, "skill_2": 1, "skill_3": 0},
        "expected": 476601,
    },
    "rosie": {
        "level": 130,
        "rank": 10,
        "skills": {"attack": 30, "skill_1": 30, "skill_2": 30, "skill_3": 2},
        "expected": 2282570,
    },
    "tarzan": {
        "level": 130,
        "rank": 3,
        "skills": {"attack": 1, "skill_1": 1, "skill_2": 1, "skill_3": 0},
        "expected": 531112,
    },
}


def calc_control(bp, hero, control):
    total = bp["level_bp"].get(str(control["level"]), 0)
    total += bp["rank_bp"].get(str(control["rank"]), 0)
    for skill, level in control["skills"].items():
        if level:
            total += bp["skill_bp"].get(hero, {}).get(skill, {}).get(str(level)) or 0
    return total


def main():
    bp = json.loads(BP_PATH.read_text(encoding="utf-8"))
    compact_bp = json.dumps(bp, ensure_ascii=False, separators=(",", ":"))
    html = HTML_PATH.read_text(encoding="utf-8")
    replacement = (
        f"    const BP = {compact_bp};\n\n"
        "    // ═══════════════════════════════════════════════════\n"
        "    // HEROES DATABASE"
    )
    updated, count = BP_PATTERN.subn(replacement, html, count=1)
    if count != 1:
        raise RuntimeError("не найдено: место встраивания const BP в Index.html")
    HTML_PATH.write_text(updated, encoding="utf-8")

    lines = [
        "cx_update_team_builder.py",
        f"embedded BP bytes={len(compact_bp.encode('utf-8'))}",
        "formula comment=формула верифицирована 4/4, 2026-06-10",
        "",
        "CONTROL VERIFICATION",
    ]
    passed = True
    for hero, control in CONTROLS.items():
        actual = calc_control(bp, hero, control)
        match = actual == control["expected"]
        passed = passed and match
        lines.append(
            f"{hero}: actual={actual}, expected={control['expected']}, "
            f"status={'PASSED' if match else 'FAILED'}"
        )
    lines.extend(
        [
            "",
            f"data verification={'PASSED' if passed else 'FAILED'}",
            "browser verification=PENDING",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not passed:
        raise RuntimeError(f"control verification failed; see {REPORT_PATH}")


if __name__ == "__main__":
    main()
