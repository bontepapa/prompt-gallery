import os
import json
import base64
import time
import requests
import sys

# Configuration
WEB_APP_URL = "https://script.google.com/macros/s/AKfycby-4JCXDGA50bcQOsHeVUokOa75erd_gqUun7IeiLgik3ZgDAgjNEO5zC-Zf11YV3XHyQ/exec"
PLAYGROUND_DIR = "/Users/gong-ganchangjo/Projects/Image_Prompt/database/playground"
RECORDS_JSON = "parsed_success_records.json"
PROGRESS_JSON = "upload_progress.json"

def main():
    if not os.path.exists(RECORDS_JSON):
        print(f"Error: {RECORDS_JSON} not found. Run list_success_details.py first.")
        sys.exit(1)

    with open(RECORDS_JSON, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Filter records that have images
    upload_queue = [r for r in records if r['has_jpg'] or r['has_png']]
    print(f"Found {len(records)} total success records.")
    print(f"Queueing {len(upload_queue)} records that have corresponding images.")

    # Load progress
    progress = {}
    if os.path.exists(PROGRESS_JSON):
        with open(PROGRESS_JSON, 'r', encoding='utf-8') as f:
            try:
                progress = json.load(f)
            except Exception:
                print("Warning: Progress file is corrupted. Starting fresh.")
                progress = {}

    print(f"Already uploaded: {len(progress)} items.")

    todo = [r for r in upload_queue if r['base_name'] not in progress]
    print(f"Remaining items to upload: {len(todo)}")

    if not todo:
        print("All items have been successfully uploaded.")
        return

    # Prompt user for single-item test run if we haven't uploaded anything yet
    test_run = False
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_run = True
        todo = todo[:1]
        print("Running in TEST mode (uploading 1 item only).")

    success_count = 0
    fail_count = 0

    for i, r in enumerate(todo):
        filename = r['jpg_name'] if r['has_jpg'] else r['png_name']
        image_path = os.path.join(PLAYGROUND_DIR, filename)
        
        print(f"[{i+1}/{len(todo)}] Uploading: {r['title']} ({filename})...")
        
        # Read and encode image to base64
        try:
            with open(image_path, 'rb') as img_f:
                img_data = img_f.read()
                b64_str = base64.b64encode(img_data).decode('utf-8')
                mime_type = "image/jpeg" if filename.endswith('.jpg') else "image/png"
                data_uri = f"data:{mime_type};base64,{b64_str}"
        except Exception as e:
            print(f"  -> Error reading image {filename}: {e}")
            fail_count += 1
            continue

        # Prepare payload
        payload = {
            "action": "upload",
            "base64": data_uri,
            "mimeType": mime_type,
            "filename": filename,
            "category": r['category'],
            "title": r['title'],
            "prompt": r['prompt'],
            "status": "success",
            "thinking": r['thinking'],
            "analysis": r['analysis']
        }

        # Attempt upload with retries
        max_retries = 3
        uploaded = False
        
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(WEB_APP_URL, data=payload, timeout=60)
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get('success'):
                        print(f"  -> Success! File URL: {res_json.get('fileUrl')}")
                        progress[r['base_name']] = {
                            "date": r['date'],
                            "title": r['title'],
                            "fileUrl": res_json.get('fileUrl'),
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        # Save progress immediately
                        with open(PROGRESS_JSON, 'w', encoding='utf-8') as prog_f:
                            json.dump(progress, prog_f, ensure_ascii=False, indent=2)
                        success_count += 1
                        uploaded = True
                        break
                    else:
                        print(f"  -> Web App returned failure (attempt {attempt}/{max_retries}): {res_json.get('error')}")
                else:
                    print(f"  -> HTTP Error {response.status_code} (attempt {attempt}/{max_retries})")
            except Exception as e:
                print(f"  -> Connection error (attempt {attempt}/{max_retries}): {e}")

            if attempt < max_retries:
                sleep_time = attempt * 3
                print(f"  -> Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

        if not uploaded:
            print("  -> Failed to upload after maximum retries.")
            fail_count += 1
            # In test mode, fail immediately
            if test_run:
                break
        
        # Polite delay to prevent Google rate limits
        if i < len(todo) - 1:
            time.sleep(1.5)

    print("\n=== Upload Summary ===")
    print(f"Successful uploads in this run: {success_count}")
    print(f"Failed uploads in this run: {fail_count}")
    print(f"Total progress: {len(progress)}/{len(upload_queue)} items uploaded.")

if __name__ == "__main__":
    main()
