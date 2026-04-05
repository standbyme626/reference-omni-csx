import json
import os
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(
    os.getenv(
        "PLATFORM_SIM_ECD_DATA_DIR",
        str(REPO_ROOT / "data" / "ecommerce_dialogue_corpus" / "E-commerce dataset"),
    )
)
OUTPUT_DIR = Path(
    os.getenv(
        "PLATFORM_SIM_QUERY_OUTPUT_DIR",
        str(REPO_ROOT / "data" / "extracted_user_queries"),
    )
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_user_messages():
    """从ECD数据集提取纯用户消息"""
    user_messages = defaultdict(list)
    
    files = ["train.txt", "dev.txt", "test.txt"]
    
    for fname in files:
        fpath = DATA_DIR / fname
        if not fpath.exists():
            continue
        
        print(f"Processing {fname}...")
        
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) < 2:
                    continue
                
                dialogue = parts[1]
                turns = dialogue.split()
                
                for i, turn in enumerate(turns):
                    if i % 2 == 0:
                        turn = turn.strip()
                        
                        if len(turn) < 3 or len(turn) > 100:
                            continue
                        
                        if re.search(r'(亲|您好|在的哦|好的呢|恩恩|可以的|稍等|帮您|小店|客官)', turn):
                            continue
                        
                        if re.search(r'(订单|发货|快递|物流|退款|退货|签收|到货)', turn):
                            user_messages['order_status'].append(turn)
                        elif re.search(r'(单号|到哪|到哪了|物流|快递)', turn):
                            user_messages['logistics'].append(turn)
                        elif re.search(r'(退款|退钱|退货|取消订单)', turn):
                            user_messages['refund'].append(turn)
    
    return user_messages

def build_templates(user_messages):
    """构建用户消息模板"""
    templates = {}
    
    for cat, messages in user_messages.items():
        unique = list(set(messages))
        unique.sort(key=len)
        templates[cat] = unique[:100]
    
    return templates

def main():
    print("Extracting user messages from ECD dataset...")
    
    user_messages = extract_user_messages()
    
    for cat, msgs in user_messages.items():
        print(f"  {cat}: {len(msgs)} messages")
    
    templates = build_templates(user_messages)
    
    output = {"prompt_templates": templates}
    
    with open(OUTPUT_DIR / "user_prompt_templates.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved to: {OUTPUT_DIR / 'user_prompt_templates.json'}")
    
    print("\n=== Sample User Messages ===")
    for cat, msgs in templates.items():
        print(f"\n{cat}:")
        for msg in msgs[:10]:
            print(f"  - {msg}")

if __name__ == "__main__":
    main()
