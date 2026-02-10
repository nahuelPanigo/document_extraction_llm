from constants import DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED, JSON_FOLDER
from utils.text_extraction.read_and_write_files import read_data_json
import re


import re

MONTHS_REGEX = re.compile(
    r"\b("
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre"
    r")\b",
    re.IGNORECASE
)

def normalize_volume_issue(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    s = text.lower()

    # 1. Remove months
    s = MONTHS_REGEX.sub("", s)

    # 2. Normalize volume (remove dots)
    s = re.sub(r"\bvol(\.|umen)?\b", "vol", s)

    # 3. Normalize issue / number (remove dots)
    s = re.sub(r"\b(número|numero|nro|nº|n°|n\.º|no\.?)\b", "no", s)

    # 4. Normalize special issue
    s = re.sub(r"\b(no\s+)?especial\b", "especial", s)

    # 5. Normalize supplement
    s = re.sub(
        r"\b(suplemento|sup)\s*(no\s*)?(\d+)",
        r"suplemento \3",
        s
    )

    # 6. Convert "(number)" AFTER volume → "no number"
    s = re.sub(
        r"(vol\s+\d+)\s*\(\s*(\d+)\s*\)",
        r"\1, no \2",
        s
    )

    # 7. Convert standalone "number (number)" → "vol number, no number"
    s = re.sub(
        r"\b(\d+)\s*\(\s*(\d+)\s*\)",
        r"vol \1, no \2",
        s
    )

    # 8. Ensure space between tokens and numbers (vol8 → vol 8, no2 → no 2)
    s = re.sub(r"\b(vol|no|suplemento)(\d+)\b", r"\1 \2", s)

    # 9. Normalize separators
    s = re.sub(r"\s*[,;|]\s*", ", ", s)

    # 10. Remove remaining parentheses
    s = re.sub(r"[()]", "", s)

    # 11. Remove duplicated "vol"
    s = re.sub(r"\bvol\s+vol\b", "vol", s)

    # 12. Cleanup spaces and commas
    s = re.sub(r"\s{2,}", " ", s)
    s = s.strip(" ,")

    return s








if __name__ == "__main__":

    dataset_path = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED
    print(f"📂 Loading dataset from: {dataset_path}")
    metadata = read_data_json(dataset_path, "utf-8")
    volumest = []
    for step in metadata:
        for record in metadata[step]:
            if "journalVolumeAndIssue" in record and record["journalVolumeAndIssue"] != None and record["journalVolumeAndIssue"] != "" and record["journalVolumeAndIssue"] != "null":
                volumest.append(record["journalVolumeAndIssue"])
    

    print(f"📊 Total volumes: {len(volumest)}")
    print(f"📊 Unique volumes: {len(set(volumest))}")
    print(f"  Volumes: {set(volumest)}")


    norm_volumes = []
    for volume in set(volumest):
        print(f"🔍 Normalizing volume: {volume}")
        normalized_volume = normalize_volume_issue(volume)
        norm_volumes.append(normalized_volume)
        print(f"  Normalized volume: {normalized_volume}")

    print(f"📊 Total normalized volumes: {len(norm_volumes)}")
    print(f"📊 Unique normalized volumes: {len(set(norm_volumes))}")
    print(f"  Normalized volumes: {set(norm_volumes)}")

