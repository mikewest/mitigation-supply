import datetime
import json
import requests
import os
from jinja2 import Environment, FileSystemLoader

#
# Step 1: Load UseCounter JSON files, and merge them into a single data structure.
# Then use that structure to build up a representation of the last ~2 months of
# data that can be passed to the template.
#
use_counters = {
    'CrossOriginOpenerPolicySameOrigin': 3197,
    'CrossOriginOpenerPolicySameOriginAllowPopups': 3198,
    'CrossOriginEmbedderPolicyRequireCorp': 3199,
    'CoopAndCoepIsolated': 3200,

    'ContentSecurityPolicy': 15,
    'CSPWithReasonableRestrictions': 3132,
    'CSPWithBetterThanReasonableRestrictions': 3137,

    'TrustedTypesEnabled': 2722,
    'TrustedTypesEnabledEnforcing': 3160
}

days = set()
data = {}
for bucket in use_counters.values():
    response = json.loads(requests.get("https://chromestatus.com/data/timeline/featurepopularity?bucket_id=%s"%(bucket)).text)
    for item in response:
        days.add(item["date"])
        if item["date"] not in data: data[item["date"]] = {}
        data[item["date"]][bucket] = item["day_percentage"] * 100

use_counter_days = sorted(days)[-60:]
use_counter_buckets = {}
for bucket in use_counters.values():
    use_counter_buckets[bucket] = []
    for day in use_counter_days:
        use_counter_buckets[bucket].append(data[day].get(bucket, 0))

#
# Step 2: Collect WPT data by gathering the most recent aligned run IDs, then using them
# to collect the most recent results. Parse through those results to build up percentage
# totals for the browsers we care about in a structure we can pass to the template.
#
wpt_data = {
    "coep": {},
    "coop": {},
    "corp": {},
    "csp":  {},
    "tt":   {}
}

def getWPTRunIDs():
    run_data = json.loads(requests.get("https://wpt.fyi/api/runs?label=master&label=experimental&aligned").text)
    run_ids = []
    for item in run_data:
        run_ids.append(item["id"])
    return run_ids

def getWPTSearchData(run_ids):
    search_url = "https://wpt.fyi/api/search?run_ids=" + ",".join(map(str, run_ids))
    return json.loads(requests.get(search_url).text)

search_data = getWPTSearchData(getWPTRunIDs())

browser_labels = []
for item in search_data["runs"]:
    browser_labels.append(item["browser_name"])
    for test_type in wpt_data.keys():
        wpt_data[test_type][item["browser_name"]] = { "passed": 0, "total": 0 }

for item in search_data["results"]:
    test_type = None
    if item["test"].startswith("/html/cross-origin-embedder-policy/"):
        test_type = "coep"
    elif item["test"].startswith("/html/cross-origin-opener-policy/"):
        test_type = "coop"
    elif item["test"].startswith("/fetch/cross-origin-resource-policy/"):
        test_type = "corp"
    elif item["test"].startswith("/content-security-policy/"):
        test_type = "csp"
    elif item["test"].startswith("/trusted-types/"):
        test_type = "tt"
    else:
        continue

    for i, status in enumerate(item["legacy_status"]):
        wpt_data[test_type][browser_labels[i]]["passed"] += status["passes"]
        wpt_data[test_type][browser_labels[i]]["total"] += status["total"]

#
# Step 3: Render some HTML.
#
root = os.path.dirname(os.path.abspath(__file__))
env = Environment(loader=FileSystemLoader(root))
template = env.get_template("template.html")

print(template.render(
    datestamp = datetime.date.today(),
    use_counter_days = use_counter_days,
    use_counter_buckets = use_counter_buckets,
    wpt_data = wpt_data))
