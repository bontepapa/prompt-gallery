import os
import json
import requests
import re

WEB_APP_URL = "https://script.google.com/macros/s/AKfycby-4JCXDGA50bcQOsHeVUokOa75erd_gqUun7IeiLgik3ZgDAgjNEO5zC-Zf11YV3XHyQ/exec"
PROGRESS_FILE = "/Users/gong-ganchangjo/Projects/PromptGallery/upload_progress.json"

with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
    progress = json.load(f)

specific_updates = {
    "20260701-155430__fitness__eyelevel__forest__success__v02": {
        "title": "야외 운동기구 3종 — 서울 안산자락길 숲속 (success v02)",
        "category": "야외운동기구",
        "prompt": """Editorial commercial photography of outdoor fitness equipment in a quiet summer forest setting inspired by Ansan Jarak-gil, Seoul. Eye-level perspective, 50mm lens, f/4, natural photographic depth.

Preserve the outdoor fitness equipment's silhouette, proportions, key structural elements, and color blocking exactly — dark olive-green vertical posts, silver-grey tubular frames.

The central fitness equipment zone is positioned in a sunny forest clearing, receiving full bright warm filtered summer sunlight, making the metal frames luminous with no heavy tree shadow patches.

Permeable pavers pad — gray concrete pavers with thin grass and moss joints. A refined modern bench and a partially visible barrier-free wooden deck walkway in the background.

Rich botanical diversity along the plaza edge featuring a mix of textured green ferns, low-lying Liriope grasses, broad-leaf hostas, and wild forest shrubs, presenting a varied spectrum of green shades.

Users in dynamic realistic poses:
- Left unit (Waist Twister): adult male user viewed from a side-rear quarter angle, waist twisting naturally with back toward camera.
- Center unit (Air Walker): young female user viewed from side profile, dynamic striding stride with feet on pedals.
- Right unit remains empty and clearly visible.

--no CGI, no 3D render, no plastic sheen, no harsh artificial shadows."""
    },
    "20260630-142212__playground__highangle__hanok__success__v04": {
        "title": "한옥·경포호·솔숲 연계권 하이앵글 — CG 탈피 및 성공적 조명 이식 (v04)",
        "category": "조합놀이대",
        "prompt": """real-world analog documentary snapshot of the playground structure, shot on a 35mm full-frame camera with subtle natural lens roll-off and organic camera sensor grain.

Preserve the main playground structure's exact original 3D volume, silhouette, proportions, color blocking, and components. Realistic wood grain texture on all sun-facing surfaces, producing warm specular highlights.

Intense, high-contrast, directional mid-morning summer sun from the upper-left, casting clean, short, sharp-edged shadows to the lower-right across the ground.

Set within traditional clay-tile hanok eave silhouette at the upper-right frame edge, Gangneung Gyeongpo Lake and pine forest setting.

Multi-colored EPDM patterns softly undulating, three-dimensional terrain with gentle rolling mounds, bleeding naturally off all frame edges without forming any closed ring.

Exactly three Korean children actively use safe parts of the structure with candid mid-motion snapshots and realistic organic skin textures.

--no stone borders, no concrete curbs, no decorative tile boundaries enclosing the EPDM, no CGI, no 3D render, no flat plastic textures."""
    },
    "20260630-162615__playground__highangle__forest__success__v01": {
        "title": "화담숲 가을 단풍 정원 하이앵글 — photorealism 조명 이식 및 성공 (v01)",
        "category": "조합놀이대",
        "prompt": """real-world analog documentary snapshot of the combination playground structure, shot on a 35mm full-frame camera with natural sensor grain and subtle lens roll-off.

Preserve the main playground structure's original 3D volume, silhouette, proportions, color blocking, and installed layout.

Set within vibrant maple garden with crimson and orange foliage, mature Korean pine trees, and lush green moss garden inspired by Hwadam Forest.

Strong, directional mid-morning autumn sun from the upper-left, casting clean, short, sharp-edged shadows to the lower-right across the ground for deep 3D separation.

The EPDM flooring features deep navy, terracotta, ochre yellow, and cream organic curving wave bands, bleeding naturally off all frame edges. Softly undulating 3D terrain with gentle rolling mounds of 20–40 cm.

8 Korean visitors including candid adults and children in motion with realistic skin textures and autumn casual wear.

--no stone wall, no perimeter stone tiles, no border paths, no white outlines, no CGI, no 3D render, no flat plastic shaders."""
    }
}

for k, data in specific_updates.items():
    if k in progress:
        file_url = progress[k]['fileUrl']
        m = re.search(r'/d/([^/]+)', file_url)
        file_id = m.group(1) if m else ""
        print(f"Updating {k} (File ID: {file_id})...")
        payload = {
            "action": "edit",
            "fileId": file_id,
            "category": data["category"],
            "title": data["title"],
            "prompt": data["prompt"],
            "status": "success"
        }
        res = requests.post(WEB_APP_URL, data=payload)
        print("Result:", res.json())
