# Tiles Survive Team Builder

Static Team Builder using BattlePower values extracted from Tiles Survive game
configuration data.

Open `index.html` locally or publish the repository with GitHub Pages.
Hero profiles and gear inventory can be saved separately in each visitor's
browser by explicit save buttons. Two independent team variants can use the
same saved roster and inventory for comparison. Both teams are shown
simultaneously, one below the other.

Полное описание реализованной функциональности, источников данных, формул,
архитектуры и ограничений: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md).

## Data update

The published page contains a minified embedded copy of
`research/battle_power_tables.json`.

To rebuild the source data, run the scripts from the original research
workspace containing the game configuration pack:

```powershell
python cx_export_battle_power.py
python cx_add_rarity_bp_tables.py
python cx_update_team_builder.py
python cx_verify_team_builder.py
```

The game package itself is not included in this repository.

## Verification

```powershell
python cx_verify_team_builder.py
npm install
npm test
```
