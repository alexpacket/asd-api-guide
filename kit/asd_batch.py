# asd_batch.py: nightly refresh of an image repository from a plan file
# plan.csv columns: pid,current_release,target   (target = latest | above | a release such as 17.12.6)
import csv, json, os, sys, time
from asd_client import ASDClient

REPO = os.environ.get("ASD_REPO", "./images")
os.makedirs(REPO, exist_ok=True)
c = ASDClient(os.environ["CISCO_CLIENT_ID"], os.environ["CISCO_CLIENT_SECRET"])
report = []

for row in csv.DictReader(open(sys.argv[1])):
    pid, cur, tgt = row["pid"], row["current_release"], row.get("target") or "latest"
    try:
        meta = c.metadata_by_release(pid, cur, tgt)
        rows = list(c.images(meta))
        ok = [r for r in rows if not r["exceptions"]]
        if not ok:   # metadata came back, but every image is gated
            report.append({"pid": pid, "status": "blocked",
                           "codes": sorted({e for r in rows for e in r["exceptions"]})})
            continue
        pick = ok[0]
        dest = os.path.join(REPO, pick["name"])
        if os.path.exists(dest):
            report.append({"pid": pid, "status": "already in repo", "image": pick["name"]}); continue
        d = c.download_urls(pid, pick["mdfId"], [pick["guid"]], meta["metadataTransId"])
        item = d["downloads"][0]
        if item.get("exception"):
            report.append({"pid": pid, "status": "blocked",
                           "codes": [e.get("code") for e in item["exception"]]}); continue
        sha = c.fetch(item, dest + ".part")
        if pick["sha512"] and sha.lower() != pick["sha512"].lower():
            os.remove(dest + ".part")
            report.append({"pid": pid, "status": "checksum mismatch", "image": pick["name"]}); continue
        os.rename(dest + ".part", dest)
        with open(dest + ".sha512", "w") as f:
            f.write(f'{pick["sha512"]}  {pick["name"]}\n')
        report.append({"pid": pid, "status": "downloaded", "image": pick["name"], "release": pick["release"]})
    except Exception as e:      # one bad PID must not stop the run
        report.append({"pid": pid, "status": "error", "detail": str(e)[:200]})
    time.sleep(2)               # stay well under the per-second limit

print(json.dumps(report, indent=2))
sys.exit(1 if any(r["status"] in ("blocked", "error", "checksum mismatch") for r in report) else 0)
