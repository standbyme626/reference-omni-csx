import json
import os
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(
    os.getenv(
        "PLATFORM_SIM_QUERY_OUTPUT_DIR",
        str(REPO_ROOT / "data" / "extracted_user_queries"),
    )
)
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = DATA_DIR / "user_prompt_templates.json"

def load_clean_queries():
    with open(DATA_DIR / "clean_user_queries.json", "r", encoding="utf-8") as f:
        return json.load(f)

def deduplicate_and_clean(queries):
    seen = set()
    unique = []
    for q in queries:
        q_clean = q.strip()
        if q_clean and len(q_clean) >= 5 and len(q_clean) <= 100 and q_clean not in seen:
            seen.add(q_clean)
            unique.append(q_clean)
    return unique

def build_templates():
    clean_queries = load_clean_queries()

    templates = {}
    for cat, queries in clean_queries.items():
        unique_queries = deduplicate_and_clean(queries)
        templates[cat] = unique_queries

    return templates

def main():
    print("Building enhanced prompt templates from ECD data...")

    templates = build_templates()

    output = {
        "prompt_templates": templates,
        "total_categories": len(templates),
        "total_templates": sum(len(v) for v in templates.values()),
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {OUTPUT_FILE}")
    print(f"\n=== Template Summary ===")
    for cat, tmpls in sorted(templates.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{cat}: {len(tmpls)} templates")

    print(f"\nTotal: {output['total_templates']} templates")

    print("\n=== Sample Templates ===")
    for cat in ["logistics", "refund", "order_status"]:
        print(f"\n{cat}:")
        for t in templates[cat][:5]:
            print(f"  - {t}")

if __name__ == "__main__":
    main()
