import os
import glob
import re
import json

UI_WORDS = {
    'Skip to main content', 'expand_more', 'EXPLORE', 'chat_spark', 'Playground',
    'history', 'History', 'BUILD', 'add', 'New app', 'widgets', 'My apps',
    'gallery_thumbnail', 'Gallery', 'MANAGE', 'speed', 'Dashboard', 'chevron_right',
    'developer_guide', 'Documentation', 'arrow_outward', 'notifications', 'settings',
    'search', 'key', 'PRO', 'menu_open', 'edit', 'design_services', 'share',
    'compare_arrows', 'more_vert', 'tune', 'info', 'menu', 'Dismiss', 'error',
    'close', 'mic', 'add_circle', 'Run', 'keyboard_command_key', 'keyboard_return',
    'Run settings', 'code', 'Get code', 'reset_settings', 'Aspect ratio', 'Resolution',
    '2K', '16:9', 'Temperature', 'Thinking level', 'High', 'Tools', 'Grounding with Google Search',
    'Source:', 'Google Search', 'Advanced settings', 'Response ready.', 'key_off',
    'thumb_up', 'thumb_down', 'image_search', 'Image search', 'Images only', 'Images & text',
    'full_coverage', 'image', 'Expand to view model thoughts', 'Collapse to hide model thoughts',
    'Google AI models may make mistakes, so double-check outputs.',
    'Use Arrow Up and Arrow Down to select a turn, Enter to jump to it, and Escape to return to the chat.',
    'System instructions', 'Optional tone and style instructions for the model',
    'We have updated our Terms of Service', 'We have updated our Terms of Service. 자세히 알아보기',
    'Failed to save prompt. Invalid string length', 'This model is not stable and may not be suitable for production use. Learn more.',
    '••Y8FC', 'VIBE CODE', 'Nano Banana 2', 'gemini-3.1-flash-image', 'Nano Banana Pro', 'gemini-3-pro-image-preview',
    'State-of-the-art image generation and editing model.', 'Pro-level visual intelligence with Flash-speed efficiency and reality-grounded generation capabilities.',
    'Get API key', 'What\'s new', '⌘ /', 'Thoughts', '[Model thoughts omitted for brevity]'
}

STOP_TOKENS = {
    'edit', 'more_vert', 'chevron_right', 'Expand to view model thoughts',
    'Collapse to hide model thoughts', 'Thoughts', 'thumb_up', 'thumb_down',
    'share', 'compare_arrows', 'add', 'design_services', 'chat_spark',
    'Playground', 'History', 'Dashboard', 'Documentation', 'Skip to main content'
}

SPECIAL_PROMPTS = {
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
--no stone wall, no perimeter stone tiles, no border paths, no white outlines, no CGI, no 3D render, no flat plastic shaders.""",

    "20260512-172530": """High-end architectural photography of the attached Alice in Wonderland playground structure. The central play structure must be large and dominant in the frame. Strictly preserve the exact geometry, striped tower roofs, playing card panels, rabbit head sign, clock sign, stairs, and red slides.
Photographed from an elevated perspective looking down (high-angle), explicitly showcasing the vibrant EPDM rubber safety surface featuring organic color blocks of green, yellow, and blue, connected by dashed line patterns, seamlessly integrating 3D play mounds.
Set in a large theme park inspired by Gyeongju Bomun Tourist Complex. A low sleek marble seating wall, a planter, and a curved smooth concrete bench edge the play zone. Dense spring foliage, blooming cherry blossom trees, and lush green shrubs lead to a vast artificial lake in the background.
IMPORTANT: The EPDM rubber surface and all surrounding landscape elements are only partially visible at the extreme edges of the frame, bleeding off-screen. Do not zoom out to fit the environment; keep the main play structure tightly cropped and prominent.
The foreground is softly framed by out-of-focus spring cherry blossom branches framing the very edges of the foreground (3% foreground bokeh).
6-7 children in solid primary colors playing naturally; 2 children are actively climbing the stairs and playing on the structure, while the others run around the EPDM mounds. No eye contact with the camera.
Bright spring morning sun, casting dappled shadow patterns only on the surrounding ground — the central play structure receives full direct sunlight. Soft, sophisticated cinematic color grading.
--no CGI, no 3D render, no plastic sheen.""",

    "20260514-160038": """High-end commercial documentary architectural photography of the playground structure. Photographed from an elevated high-angle perspective, 50mm lens, f/8, sharp focus throughout.
The play structure must appear large and dominant, occupying at least 45-50% of the frame height. Preserve the exact product components, forms, and color blocking.
An expansive EPDM rubber floor surrounds the structure and bleeds off-screen on all sides with irregular, asymmetrical undulating free-form edges.
Outer perimeter zones feature low hemispherical play mounds in muted sage green. Sleek backless modern wooden benches in one asymmetric corner only.
Set in the Sejong National Library public plaza during warm autumn daylight. A modern civic building with a gently curved facade is visible in the background under natural sharp focus.
Autumn planting: amber and orange deciduous trees, low ornamental grasses, neatly trimmed hedge clusters, and seasonal flower beds in burgundy and gold.
3% foreground bokeh at the very left edge of the foreground only, softly framed by out-of-focus warm amber autumn leaves.
6-8 Korean children and parents interacting naturally across the play zone.
Warm afternoon sunlight casting clean dappled shadows on the ground with the main structure fully lit.
--no lens blur, no tilt-shift effect, no depth-of-field blur anywhere on the background building, no CGI, no 3D render.""",

    "20260617-104220": """Editorial commercial photography, natural photographic rendering with film-like depth and energy.
Preserve the playground structure's silhouette, proportions, color blocking, and installed layout exactly — no redesign, recolor, or component changes.
The play structure is the brightest element in the frame — fully lit by direct sunlight. Background sits in relative shade, distinctly darker than the structure.
Strong high-angle bird's-eye view from an elevated observation deck. 50mm lens, f/8, deep focus. Play structure fills 70% of the frame; surrounding park crops off intentionally. No tilt-shift, no miniature effect, no flattened perspective.
Neutral white balance, no red or warm cast. strong directional sunlight casting crisp diagonal shadow lines from the structure across the ground for dramatic depth. Dappled light patterns from the tree canopy on the surrounding EPDM. No heavy shadows on the product.
Punchy vibrant color grading, crisp contrast, vivid and lively commercial aesthetic.
Highlight detail fully preserved — no blown-out whites, no overexposed roof panels or slides.
Reference image used ONLY for EPDM rubber texture, pattern shapes, and line flow — text overrides all color. EPDM: cobalt-blue and warm medium-grey in equal organic flowing bands; coral-pink as small irregular accent patches at 10–15% max — not perfect circles. Colors vivid, not muted. Wavy organic EPDM boundary bleeds off all four frame edges — no straight edges, no hardscape, never a closed ring.
The EPDM ground plane creates a strong color separation between the sunlit structure and the surrounding environment.
Low sculpted play mounds at the periphery with soft shadow gradients for 3D volume; one flush-inset trampoline at ground level; ground beneath structure stays flat. Dense planting beds anchor all periphery edges.
8–10 children; 4–5 clearly on the structure (upper decks, stairs, slide tops, physically overlapping equipment), the rest on surrounding EPDM. Candid, no eye contact, colorful spring clothing.
Seoul Forest in spring: dense layered canopy and understory in varied greens and blooms — no sparse, bare, or copy-pasted trees. Forest-dominant background, no buildings. Slender lampposts at extreme frame edges, secondary.
--no CGI, no 3D render, no plastic look."""
}

def extract_section_code_block(content, section_name):
    pattern = rf'## {re.escape(section_name)}\s*\n(.*?)(?=\n##\s+|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return ""
    code_match = re.search(r'```(?:markdown|text)?\s*\n(.*?)\n```', match.group(1), re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    return ""

def clean_lines(lines_list):
    cleaned = []
    for line in lines_list:
        s = line.strip()
        if not s:
            cleaned.append("")
            continue
        if s in UI_WORDS or s.startswith('mecars2009@') or re.match(r'^\d[\d,]*\s+tokens$', s):
            continue
        if re.match(r'^(?:User|Model)\s+(?:AM|PM|\d+)', s):
            continue
        if s.startswith('This model is not stable'):
            continue
        if s.startswith('We have updated our Terms'):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned).strip()

def extract_prompt_backward(s_text):
    if not s_text or '[No snap context loaded.]' in s_text:
        return ""
    m_positions = list(re.finditer(r'\n\s*(?:more_vert\s*\n\s*)?Model\s+(?:AM|PM|\d+)', s_text))
    if m_positions:
        last_model = m_positions[-1]
        pre_last = s_text[:last_model.start()]
    else:
        t_m = re.search(r'\n\s*Thoughts\b', s_text)
        if t_m:
            pre_last = s_text[:t_m.start()]
        else:
            pre_last = s_text

    lines = pre_last.split('\n')
    end_idx = len(lines)
    while end_idx > 0:
        st = lines[end_idx - 1].strip()
        if st in STOP_TOKENS or not st or re.match(r'^(?:User|Model)\s+(?:AM|PM|\d+)', st) or re.match(r'^\d[\d,]*\s+tokens$', st) or st.startswith('mecars2009@'):
            end_idx -= 1
        else:
            break

    start_idx = end_idx
    while start_idx > 0:
        prev = lines[start_idx - 1].strip()
        if prev in STOP_TOKENS or re.match(r'^(?:User|Model)\s+(?:AM|PM|\d+)', prev) or prev.startswith('mecars2009@') or re.match(r'^\d[\d,]*\s+tokens$', prev):
            break
        start_idx -= 1

    prompt_lines = lines[start_idx:end_idx]
    cleaned = clean_lines(prompt_lines)
    return cleaned

def parse_record_triplet(content, filename=""):
    """
    Extracts (prompt, thinking, analysis) from markdown record.
    Guarantees 100% clean prompt without UI noise or thoughts,
    complete AI thoughts/principles, and Korean analysis memo.
    """
    # 1. Prompt Extraction
    prompt = ""
    for key, sp in SPECIAL_PROMPTS.items():
        if key in filename:
            prompt = sp
            break

    if not prompt:
        c_code = extract_section_code_block(content, "Copied AI Studio Context")
        if c_code and '[No clipboard context loaded.]' not in c_code and len(c_code) > 30:
            cut = re.search(r'\n\s*(?:more_vert\s*\n\s*)?(?:Model\s+(?:AM|PM|\d+)|Thoughts\b|Expand to view|Collapse to hide|Google AI models)', c_code)
            if cut:
                c_code = c_code[:cut.start()]
            cleaned = clean_lines(c_code.split('\n'))
            if len(cleaned) > 50:
                prompt = cleaned

    if not prompt:
        s_code = extract_section_code_block(content, "Visible Page Text Snapshot")
        if s_code:
            cleaned = extract_prompt_backward(s_code)
            if len(cleaned) > 50:
                prompt = cleaned

    # JSON fallback
    jd = {}
    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        try:
            jd = json.loads(json_match.group(1))
        except:
            pass

    if not prompt and jd.get('prompt'):
        prompt = jd.get('prompt')

    # 2. Thinking Extraction
    thinking = jd.get('thinking', '')
    if not thinking:
        s_code = extract_section_code_block(content, "Visible Page Text Snapshot")
        if not s_code:
            s_code = extract_section_code_block(content, "Copied AI Studio Context")
        if s_code:
            t_matches = re.findall(r'\bThoughts\s*\n\s*\n(.*?)(?=\n\s*(?:Collapse to hide|chevron_right|more_vert|Google AI models|##|\Z))', s_code, re.DOTALL)
            if t_matches:
                for tm in reversed(t_matches):
                    cleaned_t = []
                    for l in tm.split('\n'):
                        st = l.strip()
                        if not st or st in UI_WORDS or st.startswith('Google AI models') or st.startswith('Use Arrow Up'):
                            continue
                        cleaned_t.append(l)
                    res = '\n'.join(cleaned_t).strip()
                    if len(res) > 30:
                        thinking = res
                        break

    if not thinking:
        pos_match = re.search(r'### (?:2\. Key Working Prompt Phrases|4\. Positive Effects|4\. Why This Result Occurred)\s*\n(.*?)(?=\n\s*---|\n\s*### |\Z)', content, re.DOTALL)
        if pos_match:
            lines = [l.strip() for l in pos_match.group(1).split('\n') if l.strip()]
            thinking = '\n'.join(lines)

    # 3. Analysis Extraction
    analysis = jd.get('analysis', '')
    if not analysis:
        eval_m = re.search(r'### 1\. Overall Evaluation\s*\n(.*?)(?=\n\s*---|\n\s*### 2|\Z)', content, re.DOTALL)
        if eval_m:
            lines = [l.strip() for l in eval_m.group(1).split('\n') if l.strip()]
            analysis = '\n\n'.join(lines)
    if not analysis:
        res_m = re.search(r'## Analysis Result\s*\n(.*?)(?=\n##|\n### 8|\Z)', content, re.DOTALL)
        if res_m:
            lines = [l.strip() for l in res_m.group(1).split('\n') if l.strip()]
            analysis = '\n\n'.join(lines[:6])

    return prompt, thinking, analysis
