"""Screen catalogue content for review. Discovery never implies eligibility or open intake."""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from policy import sources

HOUSING = re.compile(r"월세\s*지원|임차료\s*지원|임대주택|이사비|중개보수|주거환경\s*개선|전세임대")
FINANCE = re.compile(r"(?:임차|전세|전월세|임대차).{0,16}(?:대출|보증료|이자지원|반환보증)")
SETTLEMENT = re.compile(r"전입|이사|입주|주거\s*정착")
SUPPLIES = re.compile(r"생필품|생활필수품|생활용품|웰컴키트|웰컴박스")

def candidate(record):
    text = json.dumps(record,ensure_ascii=False)
    return bool(HOUSING.search(text) or FINANCE.search(text) or SETTLEMENT.search(text) and SUPPLIES.search(text))

def summarize(provider,records):
    ids = [key for key,value in records.items() if candidate(value)]
    if provider=="seoul":
        return dict(discovered=len(ids),detailRead=len(ids),detailErrors=0,detailDeferred=0)
    # Bound work per request. Advertise deferred records separately from completed requests.
    def get(key):
        try:
            sources.cached("central:"+key,lambda:sources.national_detail(key))
            return True
        except Exception:
            return False
    with ThreadPoolExecutor(max_workers=4) as pool:
        checked = sum(pool.map(get,ids[:8]))
    return dict(discovered=len(ids),detailRead=checked,detailErrors=min(8,len(ids))-checked,
                detailDeferred=max(0,len(ids)-8))

