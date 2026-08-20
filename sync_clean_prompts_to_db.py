import os
import glob
import re
import json
import time
import requests

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

def clean_lines(lines_list):
    skip_exact = {
        'more_vert', 'edit', 'thumb_up', 'thumb_down', 'chevron_right',
        'Expand to view model thoughts', 'Collapse to hide model thoughts',
        'Skip to main content', 'Run settings', 'Get API key', 'Get code',
        'Google AI models may make mistakes', 'Use Arrow Up and Arrow Down',
        'Grounding with Google Search', 'Response ready', 'key_off', 'widgets',
        'share', 'compare_arrows', 'add', 'design_services', 'chat_spark',
        'settings', 'notifications', 'search', 'key', 'PRO', 'menu_open',
        'History', 'Playground', 'Build', 'Dashboard', 'Documentation',
        'arrow_outward', 'speed', 'developer_guide', 'EXPLORE', 'BUILD', 'MANAGE',
        'New app', 'My apps', 'Gallery', 'gallery_thumbnail', 'history',
        'tune', 'info', 'menu', 'Dismiss', 'error', 'close', 'mic', 'add_circle',
        'Run', 'keyboard_command_key', 'keyboard_return', 'reset_settings',
        'Aspect ratio', 'Resolution', '2K', '16:9', 'Temperature', 'System instructions',
        'Optional tone and style instructions for the model', 'Advanced settings', 'Source:'
    }
    cleaned = []
    for line in lines_list:
        s = line.strip()
        if not s:
            cleaned.append("")
            continue
        if s in skip_exact:
            continue
        if re.match(r'^(?:User|Model)\s+(?:AM|PM|\d+)', s):
            continue
        if re.match(r'^\d[\d,]*\s+tokens$', s):
            continue
        if s.startswith('This model is not stable'):
            continue
        if s.startswith('We have updated our Terms of Service'):
            continue
        if s.startswith('Failed to save prompt'):
            continue
        if s.startswith('mecars2009@gmail.com'):
            continue
        if s == '••Y8FC' or s == 'VIBE CODE':
            continue
        cleaned.append(line)
    return '\n'.join(cleaned).strip()

def extract_prompt_final(content, filename=""):
    # 1. Copied Context
    copied_section = re.search(r'## Copied AI Studio Context\s*\n(.*?)\n##\s+', content, re.DOTALL)
    if copied_section:
        c_body = copied_section.group(1)
        code_match = re.search(r'```(?:markdown|text)?\s*\n(.*?)\n```', c_body, re.DOTALL)
        if code_match:
            c_text = code_match.group(1).strip()
            if c_text and '[No clipboard context loaded.]' not in c_text and len(c_text) > 20:
                cleaned = clean_lines(c_text.split('\n'))
                if len(cleaned) > 20:
                    return cleaned, "Copied Context"

    # 2. Snapshot (User -> Model turns)
    snap_section = re.search(r'## Visible Page Text Snapshot\s*\n(.*?)\n##\s+', content, re.DOTALL)
    if snap_section:
        s_body = snap_section.group(1)
        code_match = re.search(r'```(?:markdown|text)?\s*\n(.*?)\n```', s_body, re.DOTALL)
        if code_match:
            s_text = code_match.group(1).strip()
            if s_text and '[No snap context loaded.]' not in s_text:
                turns = re.findall(r'(?:User\s+[^\n]+|edit\s*\n\s*more_vert)\s*\n(.*?)(?=\n\s*(?:Model\s+[^\n]+|Thoughts|\Z))', s_text, re.DOTALL)
                if turns:
                    for t in reversed(turns):
                        cleaned = clean_lines(t.split('\n'))
                        if len(cleaned) > 50:
                            return cleaned, "Snapshot (User Turn)"
                
                splits = re.split(r'\n\s*(?:Model\s+[^\n]+|Thoughts)\b', s_text)
                if len(splits) > 1:
                    for chunk in reversed(splits[:-1]):
                        cleaned = clean_lines(chunk.split('\n'))
                        if len(cleaned) > 50:
                            return cleaned, "Snapshot (Pre-Model Fallback)"

    # 3. JSON
    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        try:
            jd = json.loads(json_match.group(1))
            if jd.get('prompt') and len(jd.get('prompt').strip()) > 20:
                return jd.get('prompt').strip(), "JSON"
        except:
            pass

    # 4. Special Fallbacks for known cases
    if "20260611-155908" in filename:
        fallback = """Photographed from an elevated vantage point looking steeply down at approximately 45–55 degrees, 50mm lens, f/8.
Preserve the playground structure's silhouette, proportions, key motifs, color blocking, and installed layout.
An expansive asymmetrical EPDM zone overlays the play area and bleeds off all four frame edges. One circular flush-inset trampoline is embedded at ground level, flush with the surrounding EPDM paving. The EPDM pattern features a cream base overlaid with organic amoeba-blob shapes in vivid lemon-yellow, hot magenta, and burnt orange.
A vibrant summer day at Alpensia Resort, Pyeongchang — elevated alpine leisure terrain at 700m altitude.
The play zone is set on a gently sloped alpine meadow. The perimeter is framed by Korean pine and conifer forest, their tall canopies creating a rich emerald-green wall. Neat maintained low hedges, colorful seasonal flower beds. Resort-style wooden benches and slender ornamental lighting poles. Daegwallyeong mountain ridge line beneath a deep brilliant blue summer sky with a few wispy cirrus clouds.
Natural sunlight filtered through the conifer canopy creates soft dappled light patterns.
5 Korean children are distributed across the scene: 2 to 3 children are actively playing on the structure itself — one ascending the wooden stair ramp, one on the upper windmill tower deck, one mid-slide inside the green tube slide. 2 remaining children are playing on the EPDM floor surface nearby. All children are proportionally scaled by natural perspective only.
--no CGI, no 3D render"""
        return fallback, "Special Fallback"

    return "", "NONE"

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
            
            prompt, src = extract_prompt_final(content, os.path.basename(m))
            
            # Thinking
            thinking = json_data.get('thinking') or ""
            if not thinking:
                thinking_matches = re.findall(r'Thoughts\s*\n\s*\n(.*?)\n\s*(?:Expand|Collapse|chevron_right|more_vert)', content, re.DOTALL)
                if thinking_matches:
                    thinking = '\n\n'.join([m.strip() for m in thinking_matches if m.strip() and "Expand to view" not in m])
            
            # Analysis
            analysis = json_data.get('analysis') or ""
            if not analysis:
                analysis_match = re.search(r'## Analysis Result\s*\n(.*?)(\n##|\n### 8|\Z)', content, re.DOTALL)
                if analysis_match:
                    analysis = analysis_match.group(1).strip()
                    
            all_local[base_name] = {
                'category': cat,
                'title': title,
                'prompt': prompt,
                'thinking': thinking,
                'analysis': analysis,
                'status': 'success',
                'prompt_source': src
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

    print(f"Ready to update {len(sync_queue)} records in Google Sheet with 100% clean prompts.\n")

    success_count = 0
    fail_count = 0

    for i, item in enumerate(sync_queue):
        print(f"[{i+1}/{len(sync_queue)}] Updating {item['title']} (File ID: {item['file_id'][:8]}...)...")
        
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
                        print(f"  -> SUCCESS! Prompt length: {len(item['prompt'])} chars")
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
