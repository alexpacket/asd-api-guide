# Cisco Automated Software Distribution API field guide

CiscoSE field reference for customers who want to download Cisco software from a script instead of the website, using the Cisco Automated Software Distribution (ASD) API v4.0.

Live at **https://asd.ciscose.com**

## What it covers

- What ASD is, and when Catalyst Center, Intersight or the Software Suggestion API is the better tool
- Six customer use cases: image repository refresh, change-request upgrade kits, field image audits, air-gapped staging, lifecycle data for other tools, and platforms no controller manages
- Deploying it in five steps, from entitlement to a scheduled job
- Entitlement and onboarding (SNTC and PSS), OAuth 2.0 authentication, and the API Console
- The full download flow as a step-through diagram: metadata, EULA and K9 gates, download URLs, cloud downloads, SHA-512 verification
- A request builder, a searchable table of 36 error and exception codes, and a "which path?" helper
- A claim check of common misconceptions, quotas and limits, and the places Cisco's own reference contradicts itself

## Structure

| Path | Purpose |
|---|---|
| `index.html` | The published page (single self-contained file) |
| `src/build.py` | Builds `index.html` from `src/` and the scripts in `kit/` |
| `src/body.html` | Page content and inline SVG diagrams |
| `src/data.json` | Step-through and "which path?" data |
| `src/script.js` | Page script: theme, contents highlight, step-through, request builder, error lookup |
| `src/brand.css` | SE-brand styles |
| `kit/asd_client.py` | Python client: token cache, metadata, EULA and K9, download URLs, streamed download, SHA-512 check |
| `kit/asd_batch.py` | Nightly repository refresh from a plan file, with a JSON report and a non-zero exit for alerting |
| `kit/plan.csv` | Sample plan file |
| `kit/tests/test_scenarios.py` | Offline tests against a mock of the documented API shapes |
| `404.html`, `favicon.svg`, `favicon.png` | Site extras |
| `CNAME` | Custom domain for GitHub Pages |

## Rebuild and test

```bash
python3 src/build.py                   # writes index.html (standard library only)
python3 kit/tests/test_scenarios.py    # needs: pip install -r kit/requirements.txt
```

The scripts are tested against a local mock built from Cisco's documented request and response shapes, not against Cisco's live API. Field names follow Cisco's sample requests; confirm them against the Swagger YAML in your API Console before production use.

Not an official Cisco publication. Corrections are welcome as pull requests with the supporting document and release.
