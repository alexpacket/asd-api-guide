# asd_client.py: Cisco Automated Software Distribution (ASD) API v4.0 client
# token cache, metadata lookup, EULA/K9 check, download URL, streamed download, SHA-512 check
import hashlib, os, sys, time, requests

TOKEN_URL = "https://id.cisco.com/oauth2/default/v1/token"
ASD = os.environ.get("ASD_BASE", "https://apix.cisco.com/software/v4.0")

class ASDClient:
    def __init__(self, client_id, client_secret, token_url=TOKEN_URL, base=ASD):
        self.cid, self.sec, self.token_url, self.base = client_id, client_secret, token_url, base
        self.s = requests.Session(); self.tok = None; self.exp = 0

    def token(self):
        if time.time() < self.exp:
            return self.tok
        r = self.s.post(self.token_url, data={"grant_type": "client_credentials",
                        "client_id": self.cid, "client_secret": self.sec}, timeout=30)
        r.raise_for_status(); j = r.json()
        self.tok = j["access_token"]
        self.exp = time.time() + int(j.get("expires_in", 3600)) - 300   # renew 5 min early
        return self.tok

    def post(self, path, body):
        for attempt in range(4):
            r = self.s.post(self.base + path, json=body, timeout=60,
                            headers={"Authorization": f"Bearer {self.token()}"})
            # The ASD error table reports rate and quota limits as 403, not 429
            if r.status_code in (403, 429, 502, 503, 504) and attempt < 3:
                if r.status_code == 403 and "Rate" not in r.text and "Over" not in r.text:
                    break                                  # a real permission error: stop
                time.sleep(2 ** attempt * 5); continue
            break
        if r.status_code >= 400:
            raise RuntimeError(f"{path} -> HTTP {r.status_code}: {r.text[:300]}")
        return r.json()

    @staticmethod
    def images(meta):
        """Flatten metadata -> products -> softwareTypes -> operatingSystems -> releases -> images."""
        for m in meta.get("metadata", []):
            for p in m.get("products", []):
                for st in p.get("softwareTypes", []):
                    for os_ in st.get("operatingSystems", []):
                        for rel in os_.get("releases", []):
                            for img in rel.get("images", []):
                                yield {"pid": m.get("pid"), "mdfId": p.get("mdfId"),
                                       "release": rel.get("version") or rel.get("releaseVersion"),
                                       "suggested": rel.get("isSuggested"),
                                       "name": img.get("name") or img.get("imageName"),
                                       "guid": img.get("imageGuid"),
                                       "size": img.get("size") or img.get("imageSize"),
                                       "sha512": img.get("sha512"), "md5": img.get("md5"),
                                       "exceptions": [e.get("code") for e in img.get("exception", [])]}

    def metadata_by_release(self, pid, current, output="latest", page=1):
        # Field casing follows Cisco's sample request; the parameter table spells some differently
        return self.post("/metadata/pidrelease", {"pid": pid, "currentReleaseVersion": current,
                         "outputReleaseVersion": output, "pageIndex": str(page), "perPage": "25"})

    def metadata_by_image(self, pid, image_names):
        return self.post("/metadata/pidimage", {"pid": pid, "imageNames": image_names[:5],
                         "pageIndex": "1", "perPage": "25"})

    def accept(self, kind, file_name):
        # kind is "eula" or "k9"; only call after reviewing the agreement with the right owner
        body = {"status": "Accepted", "fileNames": file_name}
        if kind == "k9":
            body.update({"busFunction": "COMM_OR_CIVIL", "confirm": "CONFIRM_CHECKED"})
        return self.post(f"/compliance/{kind}", body)

    def download_urls(self, pid, mdf_id, guids, trans_id):
        return self.post("/download/pidimage", {"pid": pid, "mdfId": str(mdf_id),
                         "imageGuids": guids[:5], "metadataTransId": trans_id})

    def fetch(self, item, dest):
        """Stream one entry of downloads[] to disk; returns the SHA-512 of the bytes written."""
        h = hashlib.sha512()
        if item.get("token"):    # image is in Cisco's cloud store: form-encoded POST, follow 302s
            r = self.s.post(item["url"], data={"X-Authentication-Control": item["token"]},
                            stream=True, allow_redirects=True, timeout=600)
        else:                    # default download URL: append the API access token
            r = self.s.get(item["url"] + "&access_token=" + self.token(),
                           stream=True, allow_redirects=True, timeout=600)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk); h.update(chunk)
        return h.hexdigest()

if __name__ == "__main__":
    pid, current = sys.argv[1], sys.argv[2]
    c = ASDClient(os.environ["CISCO_CLIENT_ID"], os.environ["CISCO_CLIENT_SECRET"])
    meta = c.metadata_by_release(pid, current, "latest")
    trans = meta["metadataTransId"]                       # valid for 60 minutes
    imgs = list(c.images(meta))
    for i in imgs:
        print(f'{i["release"]:<14} {i["name"]:<48} {i["size"]:>12}  {",".join(i["exceptions"]) or "ok"}')
    ok = [i for i in imgs if not i["exceptions"]]
    if not ok:
        sys.exit("No downloadable image: resolve the exception codes above first")
    pick = ok[0]
    d = c.download_urls(pid, pick["mdfId"], [pick["guid"]], trans)
    item = d["downloads"][0]
    if item.get("exception"):
        sys.exit(f'Download blocked: {[e.get("code") for e in item["exception"]]}')
    got = c.fetch(item, item["imageName"])
    if pick["sha512"] and got.lower() != pick["sha512"].lower():
        os.remove(item["imageName"]); sys.exit("SHA-512 mismatch: file deleted")
    print(f'{item["imageName"]} downloaded and SHA-512 verified')
