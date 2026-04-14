"""One-shot script to add ABL experience keys to commands.toml source fields."""
import pathlib

p = pathlib.Path("data/base/commands.toml")
t = p.read_text(encoding="utf-8")

# Map: command key -> extra ABL keys to add to source
abl_map = {
    "chat": "abl_9 = 20, abl_41 = 10",
    "praise": "abl_9 = 15, abl_10 = 10, abl_41 = 10",
    "serve_tea": "abl_41 = 20, abl_13 = 15",
    "clink_cups": "abl_41 = 20, abl_9 = 15",
    "hug": "abl_9 = 30, abl_11 = 10",
    "care": "abl_9 = 15, abl_13 = 10",
    "scold": "abl_10 = 20",
    "train_together": "abl_42 = 20, abl_43 = 15",
    "study": "abl_43 = 50",
    "cook": "abl_44 = 40",
    "invite_meal": "abl_9 = 20, abl_41 = 15",
    "relax_together": "abl_9 = 15",
    "tease": "abl_9 = 25, abl_11 = 15",
    "invite_follow": "abl_9 = 25, abl_10 = 15",
    "walk_together": "abl_9 = 30",
    "lap_pillow": "abl_9 = 30, abl_11 = 10",
    "kiss": "abl_9 = 80, abl_11 = 40",
    "confess": "abl_9 = 100",
    "invite_date": "abl_9 = 20",
    "hold_hands": "abl_9 = 35, abl_11 = 15",
    "date_stroll": "abl_9 = 40",
    "date_meal": "abl_9 = 25, abl_41 = 15",
    "gift": "abl_9 = 30",
    "dessert_date": "abl_9 = 20, abl_41 = 10",
    "room_visit": "abl_9 = 30, abl_11 = 10",
    "enter_room": "abl_9 = 40, abl_11 = 25",
    "date_watch_sea": "abl_9 = 50, abl_11 = 15",
    "date_tease": "abl_9 = 30, abl_11 = 40",
    "apologize": "abl_10 = 10, abl_41 = 10",
    "help_work": "abl_43 = 40, abl_10 = 15",
    "pat_cheek": "abl_9 = 20",
    "poke_cheek": "abl_9 = 20",
    "read_aloud": "abl_43 = 20, abl_41 = 15",
    "follow_rest": "abl_9 = 20",
    "escort_room": "abl_9 = 30, abl_10 = 10",
    "follow_training": "abl_42 = 30, abl_43 = 15",
    "follow_meal": "abl_9 = 25, abl_41 = 10",
    "drink_together": "abl_9 = 25, abl_41 = 15",
    "invite_dark_place": "abl_9 = 30, abl_11 = 40",
    "sleep_together": "abl_9 = 50, abl_11 = 30",
    "room_kiss": "abl_9 = 60, abl_11 = 50",
    "night_visit": "abl_11 = 60",
    "caress": "abl_9 = 60, abl_11 = 50",
}

lines = t.split("\n")
output = []
i = 0
changed = 0
while i < len(lines):
    line = lines[i]
    output.append(line)

    # Detect [[commands]] blocks
    if line.strip() == "[[commands]]":
        # Read the key line
        key_line = lines[i + 1] if i + 1 < len(lines) else ""
        key = None
        if key_line.strip().startswith("key ="):
            key = key_line.strip().split('"')[1]

        # Scan ahead to find source = line
        for j in range(i + 1, min(i + 15, len(lines))):
            stripped = lines[j].strip()
            if stripped.startswith("source = {") and key in abl_map:
                # Inject ABL keys into the source dict
                # Find the closing }
                source_line = lines[j]
                close_idx = source_line.rfind("}")
                if close_idx > 0:
                    prefix = source_line[:close_idx].rstrip()
                    if prefix.endswith(","):
                        prefix += " "
                    else:
                        prefix += ", "
                    new_source = prefix + abl_map[key] + "}"
                    output.append(lines[j])  # keep original, we'll replace below
                    # Actually we need to replace the line we just added
                    output[-1] = new_source
                    changed += 1
                break
            elif stripped.startswith("[[commands]]") or stripped.startswith("source = {}"):
                break

    i += 1

p.write_text("\n".join(output), encoding="utf-8")
print(f"Modified {changed} commands with ABL experience")
