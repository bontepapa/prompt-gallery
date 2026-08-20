import re
import json

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

def extract_clean_prompt(content, filename=""):
    """
    Extracts 100% clean, untruncated prompt text from an analysis markdown file.
    Preserves all paragraphs, negative prompts (--no...), camera settings, and details.
    Strips out all AI Studio UI buttons, tokens, and navigation text.
    """
    # 1. Try Copied AI Studio Context
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

    # 2. Try Visible Page Text Snapshot (User -> Model turns)
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

    # 3. Try JSON Summary
    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        try:
            jd = json.loads(json_match.group(1))
            if jd.get('prompt') and len(jd.get('prompt').strip()) > 20:
                return jd.get('prompt').strip(), "JSON"
        except:
            pass

    # 4. Known Special Cases (Reconstructed accurately from analysis records)
    special_cases = {
        "20260611-155908": """Photographed from an elevated vantage point looking steeply down at approximately 45–55 degrees, 50mm lens, f/8.
Preserve the playground structure's silhouette, proportions, key motifs, color blocking, and installed layout.
An expansive asymmetrical EPDM zone overlays the play area and bleeds off all four frame edges. One circular flush-inset trampoline is embedded at ground level, flush with the surrounding EPDM paving. The EPDM pattern features a cream base overlaid with organic amoeba-blob shapes in vivid lemon-yellow, hot magenta, and burnt orange.
A vibrant summer day at Alpensia Resort, Pyeongchang — elevated alpine leisure terrain at 700m altitude.
The play zone is set on a gently sloped alpine meadow. The perimeter is framed by Korean pine and conifer forest, their tall canopies creating a rich emerald-green wall. Neat maintained low hedges, colorful seasonal flower beds. Resort-style wooden benches and slender ornamental lighting poles. Daegwallyeong mountain ridge line beneath a deep brilliant blue summer sky with a few wispy cirrus clouds.
Natural sunlight filtered through the conifer canopy creates soft dappled light patterns.
5 Korean children are distributed across the scene: 2 to 3 children are actively playing on the structure itself — one ascending the wooden stair ramp, one on the upper windmill tower deck, one mid-slide inside the green tube slide. 2 remaining children are playing on the EPDM floor surface nearby. All children are proportionally scaled by natural perspective only.
--no CGI, no 3D render""",
        "20260701-155430": """Editorial commercial photography of outdoor fitness equipment in a quiet summer forest setting inspired by Ansan Jarak-gil, Seoul. Eye-level perspective, 50mm lens, f/4, natural photographic depth.
Preserve the outdoor fitness equipment's silhouette, proportions, key structural elements, and color blocking exactly — dark olive-green vertical posts, silver-grey tubular frames.
The central fitness equipment zone is positioned in a sunny forest clearing, receiving full bright warm filtered summer sunlight, making the metal frames luminous with no heavy tree shadow patches.
Permeable pavers pad — gray concrete pavers with thin grass and moss joints. A refined modern bench and a partially visible barrier-free wooden deck walkway in the background.
Rich botanical diversity along the plaza edge featuring a mix of textured green ferns, low-lying Liriope grasses, broad-leaf hostas, and wild forest shrubs, presenting a varied spectrum of green shades.
Users in dynamic realistic poses:
- Left unit (Waist Twister): adult male user viewed from a side-rear quarter angle, waist twisting naturally with back toward camera.
- Center unit (Air Walker): young female user viewed from side profile, dynamic striding stride with feet on pedals.
- Right unit remains empty and clearly visible.
--no CGI, no 3D render, no plastic sheen, no harsh artificial shadows.""",
        "20260630-142212": """real-world analog documentary snapshot of the playground structure, shot on a 35mm full-frame camera with subtle natural lens roll-off and organic camera sensor grain.
Preserve the main playground structure's exact original 3D volume, silhouette, proportions, color blocking, and components. Realistic wood grain texture on all sun-facing surfaces, producing warm specular highlights.
Intense, high-contrast, directional mid-morning summer sun from the upper-left, casting clean, short, sharp-edged shadows to the lower-right across the ground.
Set within traditional clay-tile hanok eave silhouette at the upper-right frame edge, Gangneung Gyeongpo Lake and pine forest setting.
Multi-colored EPDM patterns softly undulating, three-dimensional terrain with gentle rolling mounds, bleeding naturally off all frame edges without forming any closed ring.
Exactly three Korean children actively use safe parts of the structure with candid mid-motion snapshots and realistic organic skin textures.
--no stone borders, no concrete curbs, no decorative tile boundaries enclosing the EPDM, no CGI, no 3D render, no flat plastic textures.""",
        "20260630-162615": """real-world analog documentary snapshot of the combination playground structure, shot on a 35mm full-frame camera with natural sensor grain and subtle lens roll-off.
Preserve the main playground structure's original 3D volume, silhouette, proportions, color blocking, and installed layout.
Set within vibrant maple garden with crimson and orange foliage, mature Korean pine trees, and lush green moss garden inspired by Hwadam Forest.
Strong, directional mid-morning autumn sun from the upper-left, casting clean, short, sharp-edged shadows to the lower-right across the ground for deep 3D separation.
The EPDM flooring features deep navy, terracotta, ochre yellow, and cream organic curving wave bands, bleeding naturally off all frame edges. Softly undulating 3D terrain with gentle rolling mounds of 20–40 cm.
8 Korean visitors including candid adults and children in motion with realistic skin textures and autumn casual wear.
--no stone wall, no perimeter stone tiles, no border paths, no white outlines, no CGI, no 3D render, no flat plastic shaders."""
    }

    for key, fb_prompt in special_cases.items():
        if key in filename:
            return fb_prompt, "Special Fallback"

    return "", "NONE"
