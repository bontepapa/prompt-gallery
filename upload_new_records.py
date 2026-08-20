import os
import json
import base64
import time
import requests
import sys

WEB_APP_URL = "https://script.google.com/macros/s/AKfycby-4JCXDGA50bcQOsHeVUokOa75erd_gqUun7IeiLgik3ZgDAgjNEO5zC-Zf11YV3XHyQ/exec"
QUEUE_FILE = "/Users/gong-ganchangjo/Projects/PromptGallery/new_success_records.json"
PROGRESS_FILE = "/Users/gong-ganchangjo/Projects/PromptGallery/upload_progress.json"

def main():
    if not os.path.exists(QUEUE_FILE):
        print(f"Error: {QUEUE_FILE} not found.")
        sys.exit(1)

    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Load existing progress
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            try:
                progress = json.load(f)
            except Exception as e:
                print(f"Warning loading progress: {e}")
                progress = {}

    # Filter out already uploaded
    todo = [r for r in records if r['base_name'] not in progress]
    print(f"Total items in queue: {len(records)}")
    print(f"Already uploaded in progress file: {len(records) - len(todo)}")
    print(f"Items to upload in this session: {len(todo)}")

    if not todo:
        print("All items have already been uploaded!")
        return

    success_count = 0
    fail_count = 0

    for i, r in enumerate(todo):
        filename = r['image_filename']
        image_path = r['image_path']
        
        print(f"[{i+1}/{len(todo)}] [{r['category']}] {r['title']} ({filename})...")
        
        # Read and encode image to base64
        try:
            with open(image_path, 'rb') as img_f:
                img_data = img_f.read()
                b64_str = base64.b64encode(img_data).decode('utf-8')
                mime_type = "image/jpeg" if filename.endswith('.jpg') else "image/png"
                data_uri = f"data:{mime_type};base64,{b64_str}"
        except Exception as e:
            print(f"  -> [ERROR] Failed to read image file {image_path}: {e}")
            fail_count += 1
            continue

        payload = {
            "action": "upload",
            "base64": data_uri,
            "mimeType": mime_type,
            "filename": filename,
            "category": r['category'],
            "title": r['title'],
            "prompt": r['prompt'],
            "status": "success",
            "thinking": r.get('thinking', ''),
            "analysis": r.get('analysis', '')
        }

        max_retries = 3
        uploaded = False
        
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(WEB_APP_URL, data=payload, timeout=60)
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get('success'):
                        file_url = res_json.get('fileUrl')
                        print(f"  -> SUCCESS! Link: {file_url}")
                        progress[r['base_name']] = {
                            "date": r['date'],
                            "category": r['category'],
                            "title": r['title'],
                            "fileUrl": file_url,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        with open(PROGRESS_FILE, 'w', encoding='utf-8') as prog_f:
                            json.dump(progress, prog_f, ensure_ascii=False, indent=2)
                        success_count += 1
                        uploaded = True
                        break
                    else:
                        print(f"  -> [WARNING] Web App failure (attempt {attempt}/{max_retries}): {res_json.get('error')}")
                else:
                    print(f"  -> [WARNING] HTTP {response.status_code} (attempt {attempt}/{max_retries})")
            except Exception as e:
                print(f"  -> [WARNING] Network exception (attempt {attempt}/{max_retries}): {e}")

            if attempt < max_retries:
                sleep_time = attempt * 3
                print(f"  -> Retrying in {sleep_time}s...")
                time.sleep(sleep_time)

        if not uploaded:
            print(f"  -> [FAILED] Could not upload {filename} after {max_retries} attempts.")
            fail_count += 1

        if i < len(todo) - 1:
            time.sleep(1.5)

    print("\n=== UPLOAD COMPLETED ===")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total uploaded in progress file: {len(progress)}")

if __name__ == "__main__":
    main()
