# Offline tests for asd_client.py and asd_batch.py against a local mock of the documented
# ASD v4.0 request and response shapes. No Cisco credentials or network access needed.
#   python3 kit/tests/test_scenarios.py
import csv, hashlib, json, os, runpy, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)
DATA = b"image-bytes" * 4000
SHA = hashlib.sha512(DATA).hexdigest()
state = {"rate": 0}

def meta(pid, guid, name, sha, exc):
    return {"metadataTransId": "T-" + pid, "metadata": [{"pid": pid, "products": [{"mdfId": "111",
            "softwareTypes": [{"operatingSystems": [{"releases": [{"version": "1.0", "isSuggested": "Y",
            "images": [{"imageGuid": guid, "name": name, "size": str(len(DATA)), "sha512": sha,
                        "exception": exc}]}]}]}]}]}]}

class Mock(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def out(self, code, obj=None, raw=None, hdr=None):
        self.send_response(code)
        for k, v in (hdr or {}).items(): self.send_header(k, v)
        b = raw if raw is not None else json.dumps(obj).encode()
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/token":
            assert b"grant_type=client_credentials" in body
            return self.out(200, {"access_token": "T1", "token_type": "Bearer", "expires_in": 3599})
        if self.path == "/cloudfile":
            assert body == b"X-Authentication-Control=CT%2F9", body
            return self.out(302, raw=b"", hdr={"Location": "/final"})
        assert self.headers["Authorization"] == "Bearer T1"
        j = json.loads(body); pid = j["pid"]
        if self.path == "/sw/metadata/pidrelease":
            assert {"pid", "currentReleaseVersion", "outputReleaseVersion"} <= set(j)
            if pid == "RATE":
                state["rate"] += 1
                if state["rate"] == 1:
                    return self.out(403, raw=b"<h1>Account Over Queries Per Second Limit</h1>")
            if pid == "DENY": return self.out(403, raw=b"<h1>Forbidden</h1>")
            if pid == "NODATA": return self.out(400, {"code": "NO_DATA_FOUND_FOR_PID"})
            exc = [{"code": "K9_FORM_AR"}] if pid == "GATED" else []
            sha = "00" * 64 if pid == "BADSHA" else SHA
            return self.out(200, meta(pid, "G-" + pid, pid.lower() + ".bin", sha, exc))
        if self.path == "/sw/download/pidimage":
            assert j["metadataTransId"] == "T-" + pid and j["mdfId"] == "111" and j["imageGuids"] == ["G-" + pid]
            item = {"url": f"http://127.0.0.1:{PORT}/dl?c=1", "token": "", "imageGuid": "G-" + pid,
                    "imageName": pid.lower() + ".bin", "exception": []}
            if pid == "DLEXC": item["exception"] = [{"code": "IMG_CONTRACT_REQD"}]
            if pid == "CLOUD": item.update(url=f"http://127.0.0.1:{PORT}/cloudfile", token="CT/9")
            return self.out(200, {"sessionId": "1", "downloads": [item]})
        self.out(404, {})
    def do_GET(self):
        if self.path in ("/dl?c=1&access_token=T1", "/final"): return self.out(200, raw=DATA)
        self.out(404, {})

srv = HTTPServer(("127.0.0.1", 0), Mock); PORT = srv.server_port
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ.update(NO_PROXY="127.0.0.1", no_proxy="127.0.0.1", CISCO_CLIENT_ID="x", CISCO_CLIENT_SECRET="y")

import asd_client
asd_client.ASDClient.__init__.__defaults__ = (f"http://127.0.0.1:{PORT}/token", f"http://127.0.0.1:{PORT}/sw")
asd_client.time.sleep = lambda s: None

expected = {"OK": "downloaded", "RATE": "downloaded", "CLOUD": "downloaded", "DENY": "error",
            "NODATA": "error", "GATED": "blocked", "DLEXC": "blocked", "BADSHA": "checksum mismatch"}
with tempfile.TemporaryDirectory() as d:
    plan = os.path.join(d, "plan.csv")
    with open(plan, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["pid", "current_release", "target"])
        for p in expected: w.writerow([p, "1.0", "latest"])
    os.environ["ASD_REPO"] = os.path.join(d, "images")
    import io, contextlib
    def run():
        buf = io.StringIO(); code = 0
        sys.argv = ["asd_batch.py", plan]
        with contextlib.redirect_stdout(buf):
            try: runpy.run_path(os.path.join(KIT, "asd_batch.py"), run_name="__main__")
            except SystemExit as e: code = e.code
        return json.loads(buf.getvalue()), code
    report, code = run()
    got = {r["pid"]: r["status"] for r in report}
    for p, want in expected.items():
        print(f"{'PASS' if got.get(p) == want else 'FAIL'}  {p:<7} expected {want:<18} got {got.get(p)}")
    assert got == expected, got
    assert code == 1, "batch must exit 1 when anything is blocked or failed"
    assert not os.path.exists(os.path.join(d, "images", "badsha.bin")), "bad checksum file must be deleted"
    for p in ("ok", "rate", "cloud"):
        f = os.path.join(d, "images", p + ".bin")
        assert hashlib.sha512(open(f, "rb").read()).hexdigest() == SHA
        assert open(f + ".sha512").read().startswith(SHA)
    report2, _ = run()
    assert {r["pid"]: r["status"] for r in report2}["OK"] == "already in repo"
    print("PASS  second run skips images already in the repository")
print("All scenarios passed")
