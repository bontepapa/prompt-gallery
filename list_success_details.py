import os
import re
import json

directory = "/Users/gong-ganchangjo/Projects/Image_Prompt/database/playground"
files = os.listdir(directory)

md_files = sorted([f for f in files if f.endswith('.md')])

success_records = []

# Fallback prompt for the resort success v03 file
resort_v03_fallback_prompt = """Photographed from an elevated vantage point looking steeply down at approximately 45–55 degrees, 50mm lens, f/8.
Preserve the playground structure's silhouette, proportions, key motifs, color blocking, and installed layout.
An expansive asymmetrical EPDM zone overlays the play area and bleeds off all four frame edges. One circular flush-inset trampoline is embedded at ground level, flush with the surrounding EPDM paving. The EPDM pattern features a cream base overlaid with organic amoeba-blob shapes in vivid lemon-yellow, hot magenta, and burnt orange.
A vibrant summer day at Alpensia Resort, Pyeongchang — elevated alpine leisure terrain at 700m altitude.
The play zone is set on a gently sloped alpine meadow. The perimeter is framed by Korean pine and conifer forest, their tall canopies creating a rich emerald-green wall. Neat maintained low hedges, colorful seasonal flower beds. Resort-style wooden benches and slender ornamental lighting poles. Daegwallyeong mountain ridge line beneath a deep brilliant blue summer sky with a few wispy cirrus clouds.
Natural sunlight filtered through the conifer canopy creates soft dappled light patterns.
5 Korean children are distributed across the scene: 2 to 3 children are actively playing on the structure itself — one ascending the wooden stair ramp, one on the upper windmill tower deck, one mid-slide inside the green tube slide. 2 remaining children are playing on the EPDM floor surface nearby. All children are proportionally scaled by natural perspective only.
--no CGI, no 3D render"""

for f in md_files:
    full_path = os.path.join(directory, f)
    with open(full_path, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
        
    # Check frontmatter
    fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    fm_data = {}
    if fm_match:
        fm_lines = fm_match.group(1).split('\n')
        for line in fm_lines:
            if ':' in line:
                k, v = line.split(':', 1)
                fm_data[k.strip()] = v.strip()
                
    status = fm_data.get('status', '').lower()
    
    # Also check JSON
    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    json_data = {}
    if json_match:
        try:
            json_data = json.loads(json_match.group(1))
        except Exception:
            pass
            
    json_status = json_data.get('status', '').lower()
    
    # If it is classified as success in frontmatter or JSON
    is_success = (status in ['success', 'succcess']) or (json_status in ['success', 'succcess'])
    
    if is_success:
        base_name = f[:-3]
        # check corresponding image file
        jpg_name = base_name + '.jpg'
        png_name = base_name + '.png'
        
        has_jpg = jpg_name in files
        has_png = png_name in files
        
        # Determine prompt
        prompt = json_data.get('prompt')
        
        if not prompt:
            # Let's try matching User block
            match = re.search(r'User [^\n]*\nedit\s*\nmore_vert\s*\n\s*(.*?)\n\s*more_vert\s*\n\s*Model', content, re.DOTALL)
            if match:
                prompt = match.group(1).strip()
            else:
                match2 = re.search(r'User [^\n]*\n(?:edit\s*\n)?more_vert\s*\n\s*(.*?)\n\s*more_vert\s*\n\s*Model', content, re.DOTALL)
                if match2:
                    prompt = match2.group(1).strip()
                else:
                    match3 = re.search(r'User [^\n]*\n\s*(.*?)\n\s*Model', content, re.DOTALL)
                    if match3:
                        prompt = match3.group(1).strip()
        
        if not prompt and f == "20260611-155908__playground__highangle__resort__success__v03.md":
            prompt = resort_v03_fallback_prompt
            
        # Get category
        category = json_data.get('category') or fm_data.get('product_type')
        
        # Map category to Korean if needed
        category_map = {
            'playground': '조합놀이대',
            'pergola': '퍼걸러',
            'bench': '벤치',
            'water': '물놀이대',
            'swings': '단위놀이대',
            'pergoler': '퍼걸러',
        }
        mapped_category = category_map.get(category, category)
        
        title = json_data.get('title') or f"{mapped_category} ({fm_data.get('topic', '')} {fm_data.get('angle', '')})"
        
        # Extract AI Thinking
        thinking = json_data.get('thinking') or ""
        if not thinking:
            thinking_matches = re.findall(r'Thoughts\s*\n\s*\n(.*?)\n\s*(?:Expand|Collapse|chevron_right|more_vert)', content, re.DOTALL)
            if thinking_matches:
                thinking = '\n\n'.join([m.strip() for m in thinking_matches if m.strip() and "Expand to view" not in m])
        
        # Extract Analysis
        analysis = json_data.get('analysis') or ""
        if not analysis:
            analysis_match = re.search(r'## Analysis Result\s*\n(.*?)(\n##|\n### 8|\Z)', content, re.DOTALL)
            if analysis_match:
                analysis = analysis_match.group(1).strip()
                
        success_records.append({
            'filename': f,
            'base_name': base_name,
            'date': fm_data.get('date'),
            'category': mapped_category,
            'title': title,
            'prompt': prompt,
            'thinking': thinking,
            'analysis': analysis,
            'status': 'success',
            'has_jpg': has_jpg,
            'has_png': has_png,
            'jpg_name': jpg_name if has_jpg else None,
            'png_name': png_name if has_png else None
        })

print(f"Parsed {len(success_records)} success records.")
missing_prompts = [r for r in success_records if not r['prompt']]
print(f"Missing prompts: {len(missing_prompts)}")

# Save as json
with open('parsed_success_records.json', 'w', encoding='utf-8') as out_f:
    json.dump(success_records, out_f, ensure_ascii=False, indent=2)
