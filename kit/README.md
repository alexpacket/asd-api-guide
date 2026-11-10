# ASD companion kit

Scripts from https://asd.ciscose.com, ready to run.

| File | What it does |
|---|---|
| `asd_client.py` | Client for the Cisco Automated Software Distribution API v4.0. Run it with a PID and current release to download and verify the latest image, or import `ASDClient` in your own code. |
| `asd_batch.py` | Reads `plan.csv`, downloads each approved image once into `ASD_REPO`, verifies SHA-512, writes a `.sha512` file beside each image, prints a JSON report and exits 1 if anything was blocked or failed. |
| `plan.csv` | Sample plan: `pid,current_release,target` (target is `latest`, `above` or a specific release). |
| `tests/test_scenarios.py` | Offline tests: normal and cloud downloads, 403 rate-limit retry, permission error, unknown PID, K9 gate, contract block, checksum mismatch, and skip-if-present. |

## Prerequisites

1. An SNTC (Smart Net Total Care) entitlement, or a PSS (Partner Support Service) partner acting for the customer.
2. The API Developer role for the Cisco.com identity that will own the app, with the right contracts on its profile.
3. An app in the Cisco API Console: type Service, grant Client Credentials, with Automated Software Distribution selected.

## Run

```bash
pip install -r requirements.txt
export CISCO_CLIENT_ID=…  CISCO_CLIENT_SECRET=…
python3 asd_client.py C9300-48P 17.9.4          # one PID: download and verify
ASD_REPO=/srv/images python3 asd_batch.py plan.csv > report.json
python3 tests/test_scenarios.py                 # offline, no credentials needed
```

Keep the Client ID and Secret in a secrets store, not in code. Accept EULA and K9 agreements once, as the person entitled to make them; do not automate them silently.
