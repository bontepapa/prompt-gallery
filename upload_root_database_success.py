import os
import sys
import json
import base64
import time
import requests
import re

sys.path.append('/Users/gong-ganchangjo/Projects/PromptGallery')
from prompt_parser import parse_record_triplet

WEB_APP_URL = "https://script.google.com/macros/s/AKfycby-4JCXDGA50bcQOsHeVUokOa75erd_gqUun7IeiLgik3ZgDAgjNEO5zC-Zf11YV3XHyQ/exec"
DB_DIR = "/Users/gong-ganchangjo/Projects/Image_Prompt/database"
PROGRESS_FILE = "/Users/gong-ganchangjo/Projects/PromptGallery/upload_progress.json"

category_map = {
    'bench': '벤치',
    'fitness': '야외운동기구',
    'pergola': '퍼걸러',
    'playground': '조합놀이대',
    'table': '테이블',
    'water': '물놀이대',
    'swings': '단위놀이대'
}

# The 17 success files directly in DB_DIR
TARGET_FILES = [
    '20260818-164956__pergola__highangle__park__success__v04.md',
    '20260821-143943__bench__eyelevel__library__success__v02.md',
    '20260825-164249__bench__eyelevel__lake__success__v01.md',
    '20260826-150042__bench__eyelevel__golf__success__v01.md',
    '20260826-160929__bench__eyelevel__village__success__v02.md',
    '20260826-162156__bench__eyelevel__forest__success__v01.md',
    '20260831-171902__bench__eyelevel__ocean__success__v02.md',
    '20260901-102540__bench__highangle__library__success__v01.md',
    '20260901-174855__bench__eyelevel__plaza__success__v01.md',
    '20260901-175524__bench__lowangle__field__success__v01.md',
    '20260903-131023__bench__eyelevel__golf__success__v03.md',
    '20260922-135028__pergola__eyelevel__school__success__v01.md',
    '20260928-165119__playground__highangle__ocean__success__v01.md',
    '20261001-110739__pergola__lowangle__night__success__v03.md',
    '20261002-150153__pergola__highangle__ocean__success__v01.md',
    '20261006-174448__pergola__eyelevel__riverside__pending__v01.md',
    '20261015-142912__pergola__eyelevel__school__success__v01.md'
]

def main():
    # Load existing progress
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            try:
                progress = json.load(f)
            except Exception as e:
                print(f"Warning loading progress: {e}")
                progress = {}

    # Register the test uploaded item if not already recorded
    first_base = '20260818-164956__pergola__highangle__park__success__v04'
    if first_base not in progress:
        progress[first_base] = {
            "date": "2026-08-18 16:49:56",
            "category": "퍼걸러",
            "title": "Ueno Park pergola — successful architectural spring-film rendering with non-emissive transparent roof",
            "fileUrl": "https://drive.google.com/file/d/1zkVG8-oZCUy51rpltAW_9RCtM2DE4VIg/view?usp=drivesdk",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as prog_f:
            json.dump(progress, prog_f, ensure_ascii=False, indent=2)

    # Filter out already uploaded
    todo = [f for f in TARGET_FILES if f[:-3] not in progress]
    print(f"Total target success files: {len(TARGET_FILES)}")
    print(f"Already uploaded in progress: {len(TARGET_FILES) - len(todo)}")
    print(f"Remaining items to upload: {len(todo)}")

    if not todo:
        print("All target files have already been uploaded!")
        return

    success_count = 0
    fail_count = 0

    for i, md_file in enumerate(todo):
        base_name = md_file[:-3]
        md_path = os.path.join(DB_DIR, md_file)
        
        # Check image existence
        jpg_name = base_name + '.jpg'
        png_name = base_name + '.png'
        if os.path.exists(os.path.join(DB_DIR, jpg_name)):
            img_filename = jpg_name
            mime_type = "image/jpeg"
        elif os.path.exists(os.path.join(DB_DIR, png_name)):
            img_filename = png_name
            mime_type = "image/png"
        else:
            print(f"  -> [ERROR] Image missing for {base_name}. Skipping.")
            fail_count += 1
            continue

        img_path = os.path.join(DB_DIR, img_filename)

        with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        fm_data = {}
        if fm_match:
            for line in fm_match.group(1).split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    fm_data[k.strip()] = v.strip()

        json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
        json_data = {}
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
            except:
                t_m = re.search(r'"title":\s*"(.*?)"', json_match.group(1))
                if t_m:
                    json_data['title'] = t_m.group(1)

        raw_cat = json_data.get('category') or fm_data.get('product_type') or base_name.split('__')[1]
        cat = category_map.get(raw_cat, raw_cat)
        title = json_data.get('title')
        if not title:
            h1 = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if h1 and 'Analysis Record' not in h1.group(1):
                title = h1.group(1).strip()
        if not title:
            title = f"{cat} ({fm_data.get('topic', '')} {fm_data.get('angle', '')})"

        date = fm_data.get('date', base_name[:8])
        prompt, thinking, analysis = parse_record_triplet(content, md_file)

        print(f"\n[{i+1}/{len(todo)}] Uploading: [{cat}] {title}")
        print(f"  File: {img_filename} ({os.path.getsize(img_path) / 1024 / 1024:.2f} MB)")
        print(f"  Prompt: {len(prompt)} chars | Thinking: {len(thinking)} chars | Analysis: {len(analysis)} chars")

        try:
            with open(img_path, 'rb') as img_f:
                b64_str = base64.b64encode(img_f.read()).decode('utf-8')
                data_uri = f"data:{mime_type};base64,{b64_str}"
        except Exception as e:
            print(f"  -> [ERROR] Failed to read image {img_path}: {e}")
            fail_count += 1
            continue

        payload = {
            "action": "upload",
            "base64": data_uri,
            "mimeType": mime_type,
            "filename": img_filename,
            "category": cat,
            "title": title,
            "prompt": prompt,
            "status": "success",
            "thinking": thinking,
            "analysis": analysis
        }

        max_retries = 3
        uploaded = False

        for attempt in range(1, max_retries + 1):
            try:
                t0 = time.time()
                response = requests.post(WEB_APP_URL, data=payload, timeout=90)
                dur = time.time() - t0
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get('success'):
                        file_url = res_json.get('fileUrl')
                        print(f"  -> SUCCESS in {dur:.1f}s! Link: {file_url}")
                        progress[base_name] = {
                            "date": date,
                            "category": cat,
                            "title": title,
                            "fileUrl": file_url,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        with open(PROGRESS_FILE, 'w', encoding='utf-8') as prog_f:
                            json.dump(progress, prog_f, ensure_ascii=False, indent=2)
                        success_count += 1
                        uploaded = True
                        break
                    else:
                        print(f"  -> [WARNING] Web App error (attempt {attempt}/{max_retries}): {res_json.get('error')}")
                else:
                    print(f"  -> [WARNING] HTTP {response.status_code} (attempt {attempt}/{max_retries})")
            except Exception as e:
                print(f"  -> [WARNING] Network exception (attempt {attempt}/{max_retries}): {e}")

            if attempt < max_retries:
                sleep_time = attempt * 3
                print(f"  -> Retrying in {sleep_time}s...")
                time.sleep(sleep_time)

        if not uploaded:
            print(f"  -> [FAILED] Could not upload {img_filename} after {max_retries} attempts.")
            fail_count += 1

        if i < len(todo) - 1:
            time.sleep(2)

    print("\n=== BATCH UPLOAD FINISHED ===")
    print(f"Successfully uploaded: {success_count}/{len(todo)}")
    print(f"Failed: {fail_count}")
    print(f"Total uploaded items in progress: {len(progress)}")

if __name__ == "__main__":
    main()
