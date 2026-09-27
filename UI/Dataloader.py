import json
import os


def load_json(path):
    if not os.path.exists(path):
        return 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return 0

    # Ensure data is a non-empty list and every item contains the 'headline' key
    if not isinstance(data, list) or not data:
        return 0

    # Validate that every dictionary in the list has a 'headline' key
    if any("headline" not in item for item in data):
        return 0

    return data