# Builds index.html from src/ and the scripts in kit/. Python 3, standard library only.
import html, json, os, re
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
def rd(*p): return open(os.path.join(*p), encoding='utf-8').read()
css=rd(HERE,'brand.css')
extra="""<style>
#rb .fields { grid-template-columns: 1fr 1fr 1fr 2fr; }
#err-q { font-family: var(--mono); }
.hero code { font-size: .9em; }
.pb .chain li { font-size: 13.5px; }
@media (max-width: 760px) { #rb .fields { grid-template-columns: 1fr 1fr; } }
</style>"""
body=rd(HERE,'body.html').replace('%%CLIENT%%', html.escape(rd(ROOT,'kit','asd_client.py'), quote=False)).replace('%%BATCH%%', html.escape(rd(ROOT,'kit','asd_batch.py'), quote=False))
data=json.dumps(json.loads(rd(HERE,'data.json')), ensure_ascii=False).replace('</','<\\/')
js=rd(HERE,'script.js')
fav='<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 64%22%3E%3Crect width=%2264%22 height=%2264%22 rx=%2214%22 fill=%22%2312263A%22/%3E%3Cpath d=%22M32 14v26M22 30l10 10 10-10M18 48h28%22 stroke=%22%23049FD9%22 stroke-width=%225%22 fill=%22none%22 stroke-linecap=%22round%22 stroke-linejoin=%22round%22/%3E%3C/svg%3E">'
doc=f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Cisco Automated Software Distribution API Field Guide</title>
<meta name="description" content="Field guide to the Cisco Automated Software Distribution (ASD) API v4.0: use cases, deployment, entitlement, OAuth, metadata, EULA and K9, download URLs, errors, and companion APIs.">
{fav}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
{css}
{extra}
</head><body>
{body}
<script type="application/json" id="guide-data">{data}</script>
<script>
{js}
</script>
</body></html>
"""
open(os.path.join(ROOT,'index.html'),'w',encoding='utf-8').write(doc); print('built', len(doc))
# QA: every in-page anchor resolves
ids=set(re.findall(r'id="([^"]+)"',doc))
bad=[h for h in set(re.findall(r'href="#([^"]+)"',doc)) if h not in ids]
print('broken anchors', bad)
