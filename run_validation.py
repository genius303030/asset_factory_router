import subprocess
import os

commands = [
    ("pip install -e .", "pip install -e ."),
    ("asset-factory demo", "asset-factory demo"),
    ("asset-factory create tactical_panel", "asset-factory create --brief examples/tactical_panel_brief.json --out output/tactical_panel_pack"),
    ("asset-factory create ai_life_game", "asset-factory create --brief examples/ai_life_game_brief.json --out output/ai_life_game_pack"),
    ("asset-factory create construction_ad", "asset-factory create --brief examples/construction_ad_brief.json --out output/construction_ad_pack"),
    ("asset-factory create game_ui_asset", "asset-factory create --brief examples/game_ui_asset_brief.json --out output/game_ui_asset_pack"),
    ("asset-factory route", "asset-factory route --task image --style tactical_ui --quality high --budget medium"),
    ("asset-factory list-providers", "asset-factory list-providers"),
    ("asset-factory validate", "asset-factory validate --brief examples/tactical_panel_brief.json"),
    ("asset-factory inspect", "asset-factory inspect --pack output/tactical_panel_pack"),
    ("python -m unittest discover tests", "python -m unittest discover tests")
]

with open("V0.2_LOCKED_VALIDATION_LOG.md", "w", encoding="utf-8") as f:
    f.write("# V0.2 LOCKED VALIDATION LOG\n\n")
    for name, cmd in commands:
        f.write(f"## {name}\n")
        f.write(f"`{cmd}`\n\n")
        f.write("```text\n")
        
        try:
            res = subprocess.run(cmd.split(), capture_output=True, text=True)
            output = res.stdout + res.stderr
            f.write(output.strip() + "\n")
        except Exception as e:
            f.write(f"Error: {e}\n")
            
        f.write("```\n\n")

print("Validation log created.")
