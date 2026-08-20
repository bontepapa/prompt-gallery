import os
import glob
import re
import json
import time
import requests
from prompt_parser import parse_record_triplet

WEB_APP_URL = "https://script.google.com/macros/s/AKfycby-4JCXDGA50bcQOsHeVUokOa75erd_gqUun7IeiLgik3ZgDAgjNEO5zC-Zf11YV3XHyQ/exec"
PROGRESS_FILE = "/Users/gong-ganchangjo/Projects/PromptGallery/upload_progress.json"

TARGET_DIRS = [
    '/Users/gong-ganchangjo/Projects/Image_Prompt/database/bench',
    '/Users/gong-ganchangjo/Projects/Image_Prompt/database/fitness',
    '/Users/gong-ganchangjo/Projects/Image_Prompt/database/pergola',
    '/Users/gong-ganchangjo/Projects/Image_Prompt/database/playground',
    '/Users/gong-ganchangjo/Projects/Image_Prompt/database/table'
]

category_map = {
    'bench': '벤치',
    'fitness': '야외운동기구',
    'pergola': '퍼걸러',
    'playground': '조합놀이대',
    'table': '테이블',
    'water': '물놀이대',
    'swings': '단위놀이대'
}

def main():
    if not os.path.exists(PROGRESS_FILE):
        print(f"Error: {PROGRESS_FILE} not found.")
        return

    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        progress = json.load(f)

    print(f"Loaded {len(progress)} items from {PROGRESS_FILE}.")

    # Collect all local MD success data
    all_local = {}
    for d in TARGET_DIRS:
        d_name = os.path.basename(d)
        for m in sorted(glob.glob(d + '/*.md')):
            with open(m, encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            is_success = ('status: success' in content) or ('status: succcess' in content)
            if not is_success:
                continue
                
            base_name = os.path.basename(m)[:-3]
            
            # Frontmatter
            fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            fm_data = {}
            if fm_match:
                for line in fm_match.group(1).split('\n'):
                    if ':' in line:
                        k, v = line.split(':', 1)
                        fm_data[k.strip()] = v.strip()
                        
            # JSON
            json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
            json_data = {}
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                except:
                    pass
                    
            raw_cat = json_data.get('category') or fm_data.get('product_type') or d_name
            cat = category_map.get(raw_cat, category_map.get(d_name, raw_cat))
            title = json_data.get('title') or f"{cat} ({fm_data.get('topic', '')} {fm_data.get('angle', '')})"
            
            prompt, thinking, analysis = parse_record_triplet(content, os.path.basename(m))
                    
            all_local[base_name] = {
                'category': cat,
                'title': title,
                'prompt': prompt,
                'thinking': thinking,
                'analysis': analysis,
                'status': 'success'
            }

    print(f"Parsed {len(all_local)} local success records.")

    # Match with progress items to get fileId
    sync_queue = []
    for k, prog_item in progress.items():
        file_url = prog_item.get('fileUrl', '')
        m = re.search(r'/d/([^/]+)', file_url)
        file_id = m.group(1) if m else ""
        
        if not file_id:
            continue
            
        local_data = all_local.get(k)
        if not local_data:
            continue
            
        sync_queue.append({
            'base_name': k,
            'file_id': file_id,
            'category': local_data['category'],
            'title': local_data['title'],
            'prompt': local_data['prompt'],
            'thinking': local_data['thinking'],
            'analysis': local_data['analysis'],
            'status': 'success'
        })

    print(f"Ready to update {len(sync_queue)} records in Google Sheet with 100% pure prompt, thinking, and analysis.\n")

    success_count = 0
    fail_count = 0

    for i, item in enumerate(sync_queue):
        print(f"[{i+1}/{len(sync_queue)}] Updating {item['title']} (File ID: {item['file_id'][:8]}...)...")
        print(f"  -> Prompt: {len(item['prompt'])} chars | Thinking: {len(item['thinking'])} chars | Analysis: {len(item['analysis'])} chars")
        
        payload = {
            "action": "edit",
            "fileId": item['file_id'],
            "category": item['category'],
            "title": item['title'],
            "prompt": item['prompt'],
            "thinking": item['thinking'],
            "analysis": item['analysis'],
            "status": item['status']
        }
        
        updated = False
        for attempt in range(1, 4):
            try:
                res = requests.post(WEB_APP_URL, data=payload, timeout=30)
                if res.status_code == 200:
                    rj = res.json()
                    if rj.get('success'):
                        print(f"  -> SUCCESS!")
                        success_count += 1
                        updated = True
                        break
                    else:
                        print(f"  -> [WARNING] Attempt {attempt}: {rj.get('error')}")
                else:
                    print(f"  -> [WARNING] Attempt {attempt} HTTP {res.status_code}")
            except Exception as e:
                print(f"  -> [WARNING] Attempt {attempt} error: {e}")
                
            if attempt < 3:
                time.sleep(2)
                
        if not updated:
            print(f"  -> [FAILED] Could not update {item['base_name']}")
            fail_count += 1
            
        if i < len(sync_queue) - 1:
            time.sleep(1.0)

    print("\n=== BATCH CLEAN UPDATE COMPLETED ===")
    print(f"Successfully updated: {success_count}/{len(sync_queue)}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    main()
