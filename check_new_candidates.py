import os
import re
import json

TARGET_DIRS = [
    '/Users/gong-ganchangjo/Projects/Image_Prompt/database/bench',
    '/Users/gong-ganchangjo/Projects/Image_Prompt/database/fitness',
    '/Users/gong-ganchangjo/Projects/Image_Prompt/database/pergola',
    '/Users/gong-ganchangjo/Projects/Image_Prompt/database/playground',
    '/Users/gong-ganchangjo/Projects/Image_Prompt/database/table'
]

PROGRESS_FILE = "/Users/gong-ganchangjo/Projects/PromptGallery/upload_progress.json"

# Load progress file
uploaded_keys = set()
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        prog = json.load(f)
        uploaded_keys = set(prog.keys())

print(f"Total entries in upload_progress.json: {len(uploaded_keys)}")

summary_by_dir = {}
all_success_records = []

for d in TARGET_DIRS:
    d_name = os.path.basename(d)
    if not os.path.exists(d):
        continue
    
    files = os.listdir(d)
    md_files = sorted([f for f in files if f.endswith('.md')])
    
    dir_success = []
    
    for f in md_files:
        base_name = f[:-3]
        full_path = os.path.join(d, f)
        
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            
        # Check frontmatter
        fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        fm_data = {}
        if fm_match:
            for line in fm_match.group(1).split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    fm_data[k.strip()] = v.strip()
                    
        status = fm_data.get('status', '').lower()
        
        # Check JSON
        json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
        json_data = {}
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
            except Exception:
                pass
        json_status = json_data.get('status', '').lower()
        
        is_success = (status in ['success', 'succcess']) or (json_status in ['success', 'succcess'])
        
        if is_success:
            jpg_name = base_name + '.jpg'
            png_name = base_name + '.png'
            has_jpg = jpg_name in files
            has_png = png_name in files
            has_img = has_jpg or has_png
            
            is_already_uploaded = base_name in uploaded_keys
            
            rec = {
                'dir': d_name,
                'filename': f,
                'base_name': base_name,
                'date': fm_data.get('date'),
                'title': json_data.get('title') or fm_data.get('topic'),
                'has_img': has_img,
                'uploaded': is_already_uploaded
            }
            dir_success.append(rec)
            all_success_records.append(rec)
            
    summary_by_dir[d_name] = {
        'total_md': len(md_files),
        'success_total': len(dir_success),
        'already_uploaded': sum(1 for r in dir_success if r['uploaded']),
        'new_to_upload': sum(1 for r in dir_success if not r['uploaded'] and r['has_img']),
        'missing_image': sum(1 for r in dir_success if not r['has_img'])
    }

print("\n=== Directory Summary ===")
for k, v in summary_by_dir.items():
    print(f"[{k}] 총 MD: {v['total_md']} | 성공작: {v['success_total']} (기존 업로드됨: {v['already_uploaded']}, 새로 업로드할 대상: {v['new_to_upload']}, 이미지 누락: {v['missing_image']})")

total_new = sum(v['new_to_upload'] for v in summary_by_dir.values())
total_already = sum(v['already_uploaded'] for v in summary_by_dir.values())
print(f"\n전체 합계: 기 업로드 완료 {total_already}개, 신규 업로드 대상 {total_new}개")
