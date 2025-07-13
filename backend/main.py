import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import httpx

# 1) Load .env
load_dotenv()
CB_KEY = os.getenv("CRUNCHBASE_API_KEY")
W_KEY = os.getenv("WAPPALYZER_API_KEY")
if not CB_KEY or not W_KEY:
    raise RuntimeError("Set CRUNCHBASE_API_KEY and WAPPALYZER_API_KEY in .env")

# 2) Init app
app = FastAPI(title="DealPilot API")
app.add_middleware(
  CORSMiddleware,
  allow_origins=["chrome-extension://*"],
  allow_methods=["*"],
  allow_headers=["*"],
)

# 3) Endpoint
@app.post("/scrape")
async def scrape(request: Request):
    j = await request.json()
    url = j.get("url", "")
    if "linkedin.com/company/" not in url:
        raise HTTPException(400, "Must be a LinkedIn company URL")
    slug = url.rstrip("/").split("linkedin.com/company/")[1]
    # Parallel fetches
    async with httpx.AsyncClient() as client:
        cb = await _get_crunchbase(slug, client)
        wa = await _get_wappalyzer(slug + ".com", client)
    return {"company_slug": slug, "funding_info": cb, "tech_stack": wa}

# 4) Helpers
async def _get_crunchbase(slug: str, client: httpx.AsyncClient):
    url = f"https://api.crunchbase.com/api/v4/entities/organizations/{slug}?card_ids=funding_rounds"
    r = await client.get(url, headers={"X-cb-user-key": CB_KEY}, timeout=10)
    if r.status_code != 200:
        return {"error": f"Crunchbase {r.status_code}"}
    d = r.json()
    props = d.get("properties", {})
    rounds = d.get("cards", {}).get("funding_rounds", {}).get("items", [])
    return {
        "name": props.get("name"),
        "total_funding_usd": props.get("total_funding_usd"),
        "rounds_count": len(rounds),
        "latest_round": rounds[0] if rounds else None
    }

async def _get_wappalyzer(domain: str, client: httpx.AsyncClient):
    url = f"https://api.wappalyzer.com/v2/lookup/?urls=https://{domain}"
    r = await client.get(url, headers={"x-api-key": W_KEY}, timeout=10)
    if r.status_code != 200:
        return [{"error": f"Wappalyzer {r.status_code}"}]
    arr = r.json()
    techs = arr[0].get("technologies", []) if arr else []
    return [{"name": t["name"], "categories": t.get("categories", [])} for t in techs]
