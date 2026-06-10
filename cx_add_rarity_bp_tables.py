import json
from pathlib import Path

import cx_export_battle_power as ex
import cx_find_pve_effect_table as cfg


ROOT = Path(r"D:\Projects\TilesSurvive")
BP_PATH = ROOT / "research" / "battle_power_tables.json"

RARITY_HEROES = {
    "SSR": "becca",
    "ORANGE": "lucky_orange",
    "SR": "sarge",
    "R": "tim",
}

RANK_HEROES = {
    "SSR": "becca",
    "ORANGE": "lucky_orange",
    "SR": "sarge",
    "R": "rusty",
}


def main():
    raw = cfg.PACK.read_bytes()
    entries = cfg.read_pack_entries(raw)
    level_page = ex.load_page(raw, entries, 24304, "SurvivorLevelMain")
    rank_page = ex.load_page(raw, entries, 24758, "SurvivorRankMain")
    bp = json.loads(BP_PATH.read_text(encoding="utf-8"))

    bp["level_bp_by_rarity"] = {}
    bp["rank_bp_by_rarity"] = {}
    for rarity, hero in RARITY_HEROES.items():
        values = {}
        for level in range(1, 131):
            value = ex.int_slot(level_page, f"survivor_{hero}_level_{level}", 6)
            if value is None:
                raise RuntimeError(f"не найдено: {hero} level {level}")
            values[str(level)] = value
        bp["level_bp_by_rarity"][rarity] = values

    for rarity, hero in RANK_HEROES.items():
        values = {}
        for rank in range(0, 11):
            segment = 0 if rank == 0 else 6
            value = ex.int_slot(rank_page, f"survivor_{hero}_rank_{rank}_{segment}", 11)
            if value is None:
                raise RuntimeError(f"не найдено: {hero} rank {rank}_{segment}")
            values[str(rank)] = value
        bp["rank_bp_by_rarity"][rarity] = values

    BP_PATH.write_text(
        json.dumps(bp, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("level130", {k: v["130"] for k, v in bp["level_bp_by_rarity"].items()})
    print("rank10", {k: v["10"] for k, v in bp["rank_bp_by_rarity"].items()})


if __name__ == "__main__":
    main()
