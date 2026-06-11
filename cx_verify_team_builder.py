import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HTML_PATH = ROOT / "site" / "index.html"
if not HTML_PATH.exists():
    HTML_PATH = ROOT / "index.html"
BP_PATH = ROOT / "research" / "battle_power_tables.json"

EXPECTED_LEVEL_150 = {
    "SSR": 640000,
    "ORANGE": 640000,
    "SR": 531200,
    "R": 364800,
}

GROUP_BONUS = {0: 0, 1: 0, 2: 0.02, 3: 0.08, 4: 0.15, 5: 0.25}


def faction_synergy(strong, bandit, airship):
    best = None
    for air_to_strong in range(airship + 1):
        strong_group = strong + air_to_strong
        bandit_group = bandit + airship - air_to_strong
        bonus = GROUP_BONUS.get(strong_group, 0) + GROUP_BONUS.get(bandit_group, 0)
        if best is None or bonus > best[0] or (bonus == best[0] and strong_group > best[1]):
            best = (bonus, strong_group, bandit_group)
    return best


def main():
    html = HTML_PATH.read_text(encoding="utf-8")
    bp = json.loads(BP_PATH.read_text(encoding="utf-8"))

    for rarity, expected in EXPECTED_LEVEL_150.items():
        levels = bp["level_bp_by_rarity"][rarity]
        assert len(levels) == 150, (rarity, len(levels))
        assert levels["150"] == expected, (rarity, levels["150"], expected)

    heroes_block = html[html.index("const HEROES"):html.index("const RARITY")]
    hero_ids = re.findall(r'\{ id: "([^"]+)",\s+name:', heroes_block)
    factions = re.findall(r'faction: "(strong|bandit|airship)"', heroes_block)
    assert len(hero_ids) == 25, len(hero_ids)
    assert len(factions) == len(hero_ids), (len(factions), len(hero_ids))
    assert "level: 120" in html
    assert 'max="150"' in html
    assert 'becka: "becca"' in html
    assert 'const STORAGE_KEY = "tiles-survive-team-builder-v1"' in html
    assert "useState(loadSavedStates)" in html
    assert "useState(loadSavedInventory)" in html
    assert "localStorage.setItem(STORAGE_KEY" in html
    assert "function saveHero(heroId)" in html
    assert "function saveInventory()" in html
    assert "Сохранить героя" in html
    assert "Сохранить инвентарь" in html
    assert "useEffect(" not in html
    assert "gear: fallback.gear" in html

    controls = {
        "two_plus_two_plus_wildcard": ((2, 2, 1), (0.10, 3, 2)),
        "five_airships": ((0, 0, 5), (0.25, 5, 0)),
        "two_strong_plus_airship": ((2, 0, 1), (0.08, 3, 0)),
        "one_plus_one_plus_three_airships": ((1, 1, 3), (0.15, 4, 1)),
    }
    for name, (inputs, expected) in controls.items():
        actual = faction_synergy(*inputs)
        assert actual == expected, (name, actual, expected)
        print(f"{name}: inputs={inputs}, result={actual}, PASSED")

    print("level 150:", EXPECTED_LEVEL_150)
    print("heroes with factions:", len(factions))
    print("verification=PASSED")


if __name__ == "__main__":
    main()
