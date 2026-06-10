import json
import math
import struct
from pathlib import Path

import cx_find_pve_effect_table as cfg


OUT_DIR = Path(r"D:\Projects\TilesSurvive\research")
BLOCK1_OUT = OUT_DIR / "cx_export_bp_block1_levels.txt"
BLOCK2_OUT = OUT_DIR / "cx_export_bp_block2_ranks.txt"
BLOCK3_OUT = OUT_DIR / "cx_export_bp_block3_skills.txt"
BLOCK4_OUT = OUT_DIR / "cx_export_bp_block4_gear.txt"
FINAL_OUT = OUT_DIR / "battle_power_tables.json"

PAGES = {
    "Benefits": 6523,
    "SurvivorLevelMain": 24304,
    "SurvivorRankMain": 24758,
    "SurvivorSkillMain": 25141,
    "SurvivorEquipmentLevelNpp": 24146,
}

PLAYABLE_HEROES = [
    "rusty", "tim", "lucky", "sarge", "ken", "freja", "travis", "eva",
    "chief_female", "chief_male", "rosie", "nikola", "ray", "becca",
    "layla", "candy", "mike", "tony", "maddie", "lucky_orange",
    "sarge_orange", "freja_orange", "ken_orange", "travis_orange",
    "eva_orange", "wright", "tithi", "tara", "jacob", "tarzan", "chiron",
    "shark", "ragnar", "knotty", "undine",
]

VERIFIED_SSR_HEROES = ["becca", "tara", "rosie", "tarzan"]


def load_page(raw, entries, page, expected_class):
    entry = next((item for item in entries if item["page"] == page), None)
    if entry is None:
        raise RuntimeError(f"не найдено: page {page} ({expected_class})")
    data = raw[page * cfg.PAGE_SIZE:page * cfg.PAGE_SIZE + entry["size"]]
    if data[:4] != cfg.CFG_MAGIC:
        raise RuntimeError(f"не найдено: CFG magic page {page}")
    class_name = cfg.read_class_name(data)
    if class_name != expected_class:
        raise RuntimeError(
            f"page {page}: expected class {expected_class}, got {class_name}"
        )
    row_ids = cfg.read_row_ids(data)
    offsets, record_size, total_records = cfg.read_records(data, row_ids)
    return {
        "page": page,
        "class_name": class_name,
        "data": data,
        "row_ids": row_ids,
        "offsets": offsets,
        "record_size": record_size,
        "total_records": total_records,
    }


def int_slot(page_info, row_id, slot):
    if row_id not in page_info["row_ids"]:
        return None
    index = page_info["row_ids"].index(row_id)
    offset = page_info["offsets"][index] + slot * 4
    if offset + 4 > len(page_info["data"]):
        return None
    return struct.unpack_from("<i", page_info["data"], offset)[0]


def export_block1(raw, entries):
    page = load_page(raw, entries, PAGES["SurvivorLevelMain"], "SurvivorLevelMain")
    canonical_hero = "becca"
    level_bp = {}
    missing = []
    for level in range(1, 131):
        row_id = f"survivor_{canonical_hero}_level_{level}"
        value = int_slot(page, row_id, 6)
        if value is None:
            missing.append(row_id)
        else:
            level_bp[str(level)] = value

    curve_mismatches = []
    for hero in VERIFIED_SSR_HEROES:
        for level in range(1, 131):
            row_id = f"survivor_{hero}_level_{level}"
            value = int_slot(page, row_id, 6)
            expected = level_bp.get(str(level))
            if value is None:
                curve_mismatches.append((hero, level, "не найдено", expected))
            elif value != expected:
                curve_mismatches.append((hero, level, value, expected))

    control = level_bp.get("130")
    verified = (
        len(level_bp) == 130
        and not missing
        and not curve_mismatches
        and control == 390289
    )
    lines = [
        "BLOCK 1 - SurvivorLevelMain",
        f"source page={page['page']}",
        f"class_name={page['class_name']}",
        "BattlePower field=slot6",
        f"canonical hero={canonical_hero}",
        f"levels exported={len(level_bp)}/130",
        f"missing rows={missing if missing else 'не найдено'}",
        f"verified SSR heroes={', '.join(VERIFIED_SSR_HEROES)}",
        f"SSR curve mismatches={curve_mismatches if curve_mismatches else 'не найдено'}",
        "note=lower-rarity heroes have separate level curves; they are not substituted into level_bp",
        "",
        "LEVEL_BP",
    ]
    lines.extend(f"{level}={level_bp.get(str(level), 'не найдено')}" for level in range(1, 131))
    lines.extend(
        [
            "",
            "VERIFICATION",
            f"level 130 BattlePower={control if control is not None else 'не найдено'}",
            "expected=390289",
            f"status={'PASSED' if verified else 'FAILED'}",
        ]
    )
    BLOCK1_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not verified:
        raise RuntimeError(f"Block 1 verification failed; see {BLOCK1_OUT}")
    return level_bp


def export_block2(raw, entries):
    page = load_page(raw, entries, PAGES["SurvivorRankMain"], "SurvivorRankMain")
    canonical_hero = "becca"
    rank_bp = {}
    missing = []
    for rank in range(0, 11):
        segment = 0 if rank == 0 else 6
        row_id = f"survivor_{canonical_hero}_rank_{rank}_{segment}"
        value = int_slot(page, row_id, 11)
        if value is None:
            missing.append(row_id)
            rank_bp[str(rank)] = None
        else:
            rank_bp[str(rank)] = value

    controls = {
        "becca_rank_3_6": int_slot(page, "survivor_becca_rank_3_6", 11),
        "tarzan_rank_3_6": int_slot(page, "survivor_tarzan_rank_3_6", 11),
        "rosie_rank_10_6": int_slot(page, "survivor_rosie_rank_10_6", 11),
    }
    becca_rank3_segments = {
        str(segment): int_slot(page, f"survivor_becca_rank_3_{segment}", 11)
        for segment in range(1, 7)
    }
    verified = (
        not missing
        and controls["becca_rank_3_6"] == 139623
        and controls["tarzan_rank_3_6"] == 139623
        and controls["rosie_rank_10_6"] == 1076911
    )
    lines = [
        "BLOCK 2 - SurvivorRankMain",
        f"source page={page['page']}",
        f"class_name={page['class_name']}",
        "BattlePower field=slot11",
        f"canonical hero={canonical_hero}",
        "semantics=cumulative BattlePower at the current rank and segment",
        f"missing rows={missing if missing else 'не найдено'}",
        "",
        "RANK_BP (full rank: segment 6; rank 0 uses segment 0)",
    ]
    lines.extend(
        f"{rank}={rank_bp[str(rank)] if rank_bp[str(rank)] is not None else 'не найдено'}"
        for rank in range(0, 11)
    )
    lines.extend(
        [
            "",
            "BECCA RANK 3 SEGMENTS (proves cumulative structure)",
        ]
    )
    lines.extend(f"3_{segment}={value}" for segment, value in becca_rank3_segments.items())
    lines.extend(
        [
            "",
            "VERIFICATION",
            f"Becca rank 3 full={controls['becca_rank_3_6']} expected=139623",
            f"Tarzan rank 3 full={controls['tarzan_rank_3_6']} expected from screenshot/formula=139623",
            "requested Tarzan control 100191=не найдено; real nearby table value is Becca/Tarzan rank_3_2=100221",
            f"Rosie rank 10 full={controls['rosie_rank_10_6']} expected=1076911",
            f"status={'PASSED' if verified else 'FAILED'}",
        ]
    )
    BLOCK2_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not verified:
        raise RuntimeError(f"Block 2 verification failed; see {BLOCK2_OUT}")
    return rank_bp


def skill_row_id(hero, skill, level):
    if skill == "attack" and level == 1:
        return f"survivor_{hero}_attack"
    return f"survivor_{hero}_{skill}_{level}"


def export_block3(raw, entries):
    page = load_page(raw, entries, PAGES["SurvivorSkillMain"], "SurvivorSkillMain")
    skills = ("attack", "skill_1", "skill_2", "skill_3")
    skill_bp = {}
    missing = []
    for hero in PLAYABLE_HEROES:
        skill_bp[hero] = {}
        for skill in skills:
            levels = {}
            for level in range(1, 41):
                row_id = skill_row_id(hero, skill, level)
                value = int_slot(page, row_id, 9)
                levels[str(level)] = value
                if value is None:
                    missing.append(row_id)
            skill_bp[hero][skill] = levels

    controls = {
        "becca_current": sum(
            int_slot(page, row_id, 9)
            for row_id in (
                "survivor_becca_attack",
                "survivor_becca_skill_1_1",
                "survivor_becca_skill_2_5",
            )
        ),
        "tara_current": sum(
            int_slot(page, row_id, 9)
            for row_id in (
                "survivor_tara_attack",
                "survivor_tara_skill_1_1",
                "survivor_tara_skill_2_1",
            )
        ),
        "rosie_current": sum(
            int_slot(page, row_id, 9)
            for row_id in (
                "survivor_rosie_attack_30",
                "survivor_rosie_skill_1_30",
                "survivor_rosie_skill_2_30",
                "survivor_rosie_skill_3_2",
            )
        ),
        "becca_all_four_lv1": sum(
            int_slot(page, skill_row_id("becca", skill, 1), 9) for skill in skills
        ),
    }
    verified = (
        controls["becca_current"] == 4130
        and controls["tara_current"] == 1200
        and controls["rosie_current"] == 815370
    )
    lines = [
        "BLOCK 3 - SurvivorSkillMain",
        f"source page={page['page']}",
        f"class_name={page['class_name']}",
        "BattlePower field=slot9",
        f"heroes requested={len(PLAYABLE_HEROES)}",
        f"skills per hero={len(skills)}",
        "levels requested per skill=1..40",
        f"missing values={len(missing)} (stored as null; each is marked below as не найдено)",
        "",
        "SKILL_BP",
    ]
    for hero in PLAYABLE_HEROES:
        lines.append(f"[{hero}]")
        for skill in skills:
            values = skill_bp[hero][skill]
            for level in range(1, 41):
                value = values[str(level)]
                lines.append(
                    f"{hero}/{skill}/{level}="
                    f"{value if value is not None else 'не найдено'}"
                )
    lines.extend(
        [
            "",
            "VERIFICATION",
            "Becca control uses current unlocked attack lv1 + skill_1 lv1 + skill_2 lv5;",
            "locked skill_3 contributes 0.",
            f"Becca current skill BattlePower={controls['becca_current']} expected=4130",
            f"Becca all four lv1 raw table sum={controls['becca_all_four_lv1']} (not the screenshot loadout)",
            "Tara control uses current unlocked attack lv1 + skill_1 lv1 + skill_2 lv1;",
            "locked skill_3 contributes 0.",
            f"Tara current skill BattlePower={controls['tara_current']} expected=1200",
            "Rosie control uses attack/skill_1/skill_2 lv30 + skill_3 lv2.",
            f"Rosie current skill BattlePower={controls['rosie_current']} expected=815370",
            f"status={'PASSED' if verified else 'FAILED'}",
        ]
    )
    BLOCK3_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not verified:
        raise RuntimeError(f"Block 3 verification failed; see {BLOCK3_OUT}")
    return skill_bp


def read_benefit_array(page_info, row_id, slot):
    if row_id not in page_info["row_ids"]:
        return None
    index = page_info["row_ids"].index(row_id)
    field_offset = page_info["offsets"][index] + slot * 4
    pointer = struct.unpack_from("<i", page_info["data"], field_offset)[0]
    if pointer == 0:
        return {}
    target = field_offset + 4 + pointer
    if target < 0 or target + 4 > len(page_info["data"]):
        return None
    count = struct.unpack_from("<i", page_info["data"], target)[0]
    if count < 0 or count > 64:
        return None
    values_offset = target + 4 + count * 4
    if values_offset + count * 12 > len(page_info["data"]):
        return None
    result = {}
    for item in range(count):
        offset = values_offset + item * 12
        benefit_id = struct.unpack_from("<i", page_info["data"], offset)[0]
        benefit_value = struct.unpack_from("<d", page_info["data"], offset + 4)[0]
        if not math.isfinite(benefit_value):
            return None
        result[benefit_id] = benefit_value
    return result


def clean_number(value):
    if value is None:
        return None
    if float(value).is_integer():
        return int(value)
    return round(value, 8)


def compact_ui_value(value):
    if value >= 1_000_000:
        return math.floor(value / 10_000) * 10_000
    if value >= 1_000:
        return math.floor(value / 10) * 10
    return value


def export_block4(raw, entries):
    page = load_page(
        raw,
        entries,
        PAGES["SurvivorEquipmentLevelNpp"],
        "SurvivorEquipmentLevelNpp",
    )
    benefits_page = load_page(raw, entries, PAGES["Benefits"], "Benefits")
    benefit_rows = {
        "atk": "prop_hero_attack_value",
        "def": "prop_hero_defense_value",
        "hp": "prop_hero_health_value",
        "troop_atk_pct": "prop_troop_lite_attack_percent",
        "troop_def_pct": "prop_troop_lite_defense_percent",
        "troop_hp_pct": "prop_troop_lite_life_percent",
    }
    benefit_ids = {
        name: int_slot(benefits_page, row_id, 0)
        for name, row_id in benefit_rows.items()
    }
    missing_benefit_ids = [
        row_id
        for name, row_id in benefit_rows.items()
        if benefit_ids[name] is None
    ]

    parts = {"helmet": "head", "armor": "body", "legs": "leg"}
    gear_bp = {}
    missing = []
    milestone_power = {}
    for output_part, row_part in parts.items():
        gear_bp[output_part] = {}
        milestone_power[output_part] = {}
        for level in range(1, 81):
            row_id = f"equipment_suit1_{row_part}_5_level_{level}"
            benefits = read_benefit_array(page, row_id, 6)
            power = int_slot(page, row_id, 8)
            level_benefit_power = int_slot(page, row_id, 12)
            if benefits is None or power is None or level_benefit_power is None:
                missing.append(row_id)
                gear_bp[output_part][str(level)] = {
                    "bp": None,
                    "atk": None,
                    "def": None,
                    "hp": None,
                    "troop_atk_pct": None,
                    "troop_def_pct": None,
                    "troop_hp_pct": None,
                }
                continue

            item = {"bp": power + level_benefit_power}
            for name in ("atk", "def", "hp"):
                item[name] = clean_number(benefits.get(benefit_ids[name]))
            for name in ("troop_atk_pct", "troop_def_pct", "troop_hp_pct"):
                value = benefits.get(benefit_ids[name])
                item[name] = clean_number(value * 100 if value is not None else None)
            if any(value is None for value in item.values()):
                missing.append(f"{row_id}: benefit field не найдено")
            gear_bp[output_part][str(level)] = item
            milestone_power[output_part][level] = level_benefit_power

    milestone_expected = {
        "helmet": {
            10: 3000, 20: 13400, 30: 17400, 40: 32600,
            50: 32600, 60: 38600, 70: 64200, 80: 64200,
        },
        "armor": {
            10: 4320, 20: 7320, 30: 13800, 40: 17800,
            50: 17800, 60: 28600, 70: 34600, 80: 34600,
        },
        "legs": {
            10: 10400, 20: 14720, 30: 29920, 40: 36400,
            50: 36400, 60: 62000, 70: 72800, 80: 72800,
        },
    }
    milestone_mismatches = []
    for part, expected_by_level in milestone_expected.items():
        for level, expected in expected_by_level.items():
            actual = milestone_power[part].get(level)
            if actual != expected:
                milestone_mismatches.append((part, level, actual, expected))

    controls = {
        "armor_64": gear_bp["armor"]["64"],
        "legs_60": gear_bp["legs"]["60"],
        "helmet_60": gear_bp["helmet"]["60"],
    }
    expected_controls = {
        "armor_64": {"atk": 14880, "def": 5580, "hp": 930000, "bp": 471280},
        "legs_60": {"atk": 11050, "def": 1700, "hp": 1410000, "bp": 414467},
        "helmet_60": {"atk": 17850, "def": 1700, "hp": 566660, "bp": 414867},
    }
    control_mismatches = []
    for control_name, expected in expected_controls.items():
        actual = controls[control_name]
        for field, expected_value in expected.items():
            actual_value = actual[field]
            compared_value = (
                compact_ui_value(actual_value)
                if field == "hp" and actual_value is not None
                else actual_value
            )
            if compared_value != expected_value:
                control_mismatches.append(
                    (control_name, field, actual_value, compared_value, expected_value)
                )

    verified = (
        not missing_benefit_ids
        and not missing
        and not milestone_mismatches
        and not control_mismatches
        and all(len(levels) == 80 for levels in gear_bp.values())
    )
    lines = [
        "BLOCK 4 - Gold/Alloy survivor equipment",
        f"source page={page['page']}",
        f"class_name={page['class_name']}",
        f"benefit id source page={benefits_page['page']} class_name={benefits_page['class_name']}",
        "quality row pattern=equipment_suit1_{head|body|leg}_5_level_{1..80}",
        "bp formula=Power(slot8) + BenefitLvSlgPower(slot12)",
        "stats source=BenefitSlg(slot6)",
        "troop pct output=raw fraction * 100",
        f"benefit ids={benefit_ids}",
        f"missing benefit ids={missing_benefit_ids if missing_benefit_ids else 'не найдено'}",
        f"missing rows/fields={missing if missing else 'не найдено'}",
        "",
        "GEAR_BP",
    ]
    for part in ("helmet", "armor", "legs"):
        lines.append(f"[{part}]")
        for level in range(1, 81):
            lines.append(
                f"{part}/{level}="
                + json.dumps(gear_bp[part][str(level)], ensure_ascii=False, sort_keys=True)
            )
    lines.extend(["", "MILESTONE POWER VERIFICATION"])
    for part in ("helmet", "armor", "legs"):
        for level, expected in milestone_expected[part].items():
            lines.append(
                f"{part}/lv{level}: slot12={milestone_power[part].get(level)} "
                f"expected={expected}"
            )
    lines.extend(
        [
            f"milestone mismatches={milestone_mismatches if milestone_mismatches else 'не найдено'}",
            "",
            "SCREENSHOT CONTROL VERIFICATION",
            "Raw pack HP is preserved in output; screenshot controls use compact UI display values.",
        ]
    )
    for control_name, actual in controls.items():
        lines.append(
            f"{control_name}: raw={actual}; compact_ui_hp={compact_ui_value(actual['hp'])}; "
            f"expected={expected_controls[control_name]}"
        )
    lines.extend(
        [
            f"control mismatches={control_mismatches if control_mismatches else 'не найдено'}",
            f"status={'PASSED' if verified else 'FAILED'}",
        ]
    )
    BLOCK4_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not verified:
        raise RuntimeError(f"Block 4 verification failed; see {BLOCK4_OUT}")
    return gear_bp


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = cfg.PACK.read_bytes()
    entries = cfg.read_pack_entries(raw)

    level_bp = export_block1(raw, entries)
    print(f"BLOCK 1 PASSED: levels={len(level_bp)}, level130={level_bp['130']}")
    rank_bp = export_block2(raw, entries)
    print(
        f"BLOCK 2 PASSED: ranks={len(rank_bp)}, rank3={rank_bp['3']}, "
        f"rank10={rank_bp['10']}"
    )
    skill_bp = export_block3(raw, entries)
    print(f"BLOCK 3 PASSED: heroes={len(skill_bp)}")
    gear_bp = export_block4(raw, entries)
    print(f"BLOCK 4 PASSED: parts={len(gear_bp)}, levels_per_part=80")

    result = {
        "level_bp": level_bp,
        "rank_bp": rank_bp,
        "skill_bp": skill_bp,
        "gear_bp": gear_bp,
    }
    FINAL_OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"FINAL JSON WRITTEN: {FINAL_OUT}")


if __name__ == "__main__":
    main()
