# Built-in Imports
from pathlib import Path
import csv
from mido import MidiFile

seed_midi_path = Path("etc/seed_midi")
seed_midi_files = [p for p in seed_midi_path.rglob("*") if p.is_file()]

# Prepare CSV output
csv_file = "data/df_ambitus.csv"
with open(csv_file, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["file", "min_note", "max_note"])

    for file in seed_midi_files:
        midi = MidiFile(file.resolve())
        min_note = None
        max_note = None

        for track in midi.tracks:
            for msg in track:
                if msg.type in ("note_on", "note_off"):
                    note = msg.note
                    if min_note is None or note < min_note:
                        min_note = note
                    if max_note is None or note > max_note:
                        max_note = note

        writer.writerow([file.name, min_note, max_note])
