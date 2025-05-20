# scripts/generate_categories.py
# ONLY FOR DEVELOPMENT!
import httpx
import re
import json
from pathlib import Path

JS_URL = "https://thepiratebay.org/static/main.js"  # Официальный сайт, может быть заблокирован
# Альтернатива, если основной сайт недоступен и структура JS та же:
# JS_URL = "https://pirateproxy.live/static/main.js" # Пример зеркала, может меняться

OUTPUT_FILE = Path(__file__).parent.parent / "just_tbp" / "constants_generated.py"

# Regex to find category definitions in print_category function
# Example: if (cat == 101) return maintxt + 'Music'+'</a>';
CATEGORY_PATTERN_FUNC = re.compile(r"if \(cat == (\d+)\) return maintxt \+ '([^']+)'\+'</a>';")

# Regex to find category definitions in print_header2 <select> options
# Example: <option value="101">Music</option>
CATEGORY_PATTERN_SELECT = re.compile(r'<option value="(\d+)">([^<]+)</option>')
# Example: <optgroup label="Audio">
OPTGROUP_PATTERN_SELECT = re.compile(r'<optgroup label="([^"]+)">')

# Manually define main categories as apibay.org uses X00, X99 structure
# and the JS implies main categories like "Audio" for 1xx, "Video" for 2xx
MAIN_CAT_MAP = {
    "1": "audio",
    "2": "video",
    "3": "application",
    "4": "games",
    "5": "porn",  # From the JS
    "6": "other",
}


def fetch_js_content(url: str) -> str:
    try:
        # Some sites might require a common User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        with httpx.Client(headers=headers, follow_redirects=True, timeout=20.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        print(f"HTTP error fetching JS: {e.response.status_code} from {url}")
    except httpx.RequestError as e:
        print(f"Request error fetching JS: {e} from {url}")
    return ""


def sanitize_key(name: str) -> str:
    # Create a Python-friendly key: lowercase, replace spaces/slashes with underscores
    # Remove special chars like parentheses, hyphens (except if part of a word like 'tv-shows')
    name = name.lower()
    name = name.replace(' ', '_').replace('/', '_').replace('-', '_')
    name = re.sub(r'\(.*\)', '', name)  # remove (content)
    name = re.sub(r'[^a-z0-9_]', '', name)  # remove other special chars
    name = name.strip('_')
    if name == "3d":  # Special case for '3d'
        return "three_d"
    if not name or name[0].isdigit():  # ensure valid identifier
        name = "cat_" + name
    return name


def parse_categories(js_content: str) -> dict:
    categories = {mc: {} for mc in MAIN_CAT_MAP.values()}
    all_parsed_cats = {}  # Store by ID to avoid duplicates from different regexes

    # First pass with CATEGORY_PATTERN_SELECT (from <option> tags)
    # This is often more comprehensive for sub-categories
    current_main_label = None
    for line in js_content.splitlines():
        optgroup_match = OPTGROUP_PATTERN_SELECT.search(line)
        if optgroup_match:
            current_main_label = optgroup_match.group(1).lower()

        cat_match = CATEGORY_PATTERN_SELECT.search(line)
        if cat_match:
            cat_id = int(cat_match.group(1))
            cat_name = cat_match.group(2).strip()

            if cat_id == 0: continue  # Skip "All"

            main_cat_prefix = str(cat_id)[0]
            main_cat_key = MAIN_CAT_MAP.get(main_cat_prefix)

            if not main_cat_key and current_main_label:  # Try to map from optgroup
                for k, v in MAIN_CAT_MAP.items():
                    if current_main_label.startswith(v) or v.startswith(current_main_label):
                        main_cat_key = v
                        break

            if main_cat_key:
                sub_cat_key = sanitize_key(cat_name)
                if sub_cat_key and cat_id not in all_parsed_cats:
                    categories.setdefault(main_cat_key, {})[sub_cat_key] = cat_id
                    all_parsed_cats[cat_id] = cat_name
            else:
                print(
                    f"Warning: Could not map category ID {cat_id} ('{cat_name}') to a main category via prefix or optgroup '{current_main_label}'.")

    # Second pass with CATEGORY_PATTERN_FUNC (from print_category function)
    # This can catch categories not in <select> or provide alternative names
    for match in CATEGORY_PATTERN_FUNC.finditer(js_content):
        cat_id = int(match.group(1))
        cat_name = match.group(2).strip()

        if cat_id == 0: continue

        main_cat_prefix = str(cat_id)[0]
        main_cat_key = MAIN_CAT_MAP.get(main_cat_prefix)

        if main_cat_key:
            sub_cat_key = sanitize_key(cat_name)
            if sub_cat_key and cat_id not in all_parsed_cats:  # Add if not already found by select
                categories.setdefault(main_cat_key, {})[sub_cat_key] = cat_id
                all_parsed_cats[cat_id] = cat_name
                print(
                    f"Info: Added category from print_category: {cat_id} - {cat_name} as {main_cat_key}.{sub_cat_key}")
            elif sub_cat_key and cat_id in all_parsed_cats and categories[main_cat_key].get(sub_cat_key) != cat_id:
                # Potentially a name variation, or wrongly mapped previously. Prioritize select if structure is good.
                # This logic can get complex; for now, we just note it.
                # print(f"Info: Category ID {cat_id} ('{cat_name}') already exists, possibly with different name/key.")
                pass

    # Clean up empty main categories
    return {k: v for k, v in categories.items() if v}


def generate_constants_file_content(categories_data: dict) -> str:
    lines = [
        "# Generated by scripts/generate_categories.py. DO NOT EDIT MANUALLY.",
        "# flake8: noqa",
        "# pylint: disable=all",
        "from typing import Dict, Literal, Union\n\n",
        "# --- Numerical Category IDs (Generated) ---"
    ]

    all_ids = []
    for main_cat_name, sub_cats in categories_data.items():
        for sub_cat_key, cat_id in sorted(sub_cats.items(), key=lambda item: item[1]):
            const_name = f"{main_cat_name.upper()}_{sub_cat_key.upper()}"
            # Ensure const_name is a valid Python identifier
            const_name = re.sub(r'\W|^(?=\d)', '_', const_name)  # Replace non-alphanumeric, or if starts with digit
            if const_name.startswith('_'): const_name = "CAT" + const_name

            lines.append(f"{const_name} = {cat_id}")
            all_ids.append(cat_id)

    lines.append("\n# --- CategoryId Type (Generated) ---")
    unique_sorted_ids = sorted(list(set(all_ids)))
    category_id_type_str = "CategoryId = Literal[\n"
    for i in range(0, len(unique_sorted_ids), 5):  # Format 5 per line
        line_ids = ", ".join(map(str, unique_sorted_ids[i:i + 5]))
        category_id_type_str += f"    {line_ids},\n"
    category_id_type_str = category_id_type_str.rstrip(",\n") + "\n]"
    lines.append(category_id_type_str)

    lines.append("\n# --- Top100Category Type (Manual Definition) ---")
    lines.append("Top100Category = Union[CategoryId, Literal[\"all\", \"recent\"]]")

    lines.append("\n# --- CATEGORIES Dictionary (Generated) ---")
    lines.append("CATEGORIES: Dict[str, Dict[str, CategoryId]] = {")
    for main_cat_name, sub_cats in sorted(categories_data.items()):
        lines.append(f"    \"{main_cat_name}\": {{")
        for sub_cat_key, cat_id in sorted(sub_cats.items(), key=lambda item: item[1]):
            lines.append(f"        \"{sub_cat_key}\": {cat_id},")
        lines.append("    },")
    lines.append("}\n")

    lines.append("\n# --- Default Base URL and User Agent (Manual Definition) ---")
    lines.append("DEFAULT_BASE_URL = \"https://apibay.org\"")
    lines.append(
        "USER_AGENT = \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36\"\n")

    return "\n".join(lines)


if __name__ == "__main__":
    print(f"Fetching JS from {JS_URL}...")
    js_code = fetch_js_content(JS_URL)
    if js_code:
        print("Parsing categories...")
        parsed_cats = parse_categories(js_code)

        print("\nParsed Categories Structure:")
        print(json.dumps(parsed_cats, indent=4))

        print(f"\nGenerating Python code for constants...")
        file_content = generate_constants_file_content(parsed_cats)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(file_content)
        print(f"\nSuccessfully wrote generated constants to {OUTPUT_FILE}")
        print("Please review the generated file, especially for any duplicate or oddly named constants.")
        print(
            "You might need to manually merge this with your existing constants.py if it contains manual definitions.")
    else:
        print("Failed to fetch or process JS content.")
