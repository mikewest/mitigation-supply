import requests
import json

# CoopAndCoepIsolated = 3200
# CrossOriginEmbedderPolicyRequireCorp = 3199
# CrossOriginOpenerPolicySameOriginAllowPopups = 3198
# CrossOriginOpenerPolicySameOrigin = 3197
use_counters = {
    'CrossOriginOpenerPolicySameOrigin': 3197,
    'CrossOriginOpenerPolicySameOriginAllowPopups': 3198,
    'CrossOriginEmbedderPolicyRequireCorp': 3199,
    'CoopAndCoepIsolated': 3200
}

# Step 1: Load the four JSON files, and merge them into a single data structure:
#
# data["2020-04-22"]["CoopAndCoepIsolated"] = 0.0001;
data = {}
for bucket in use_counters.values():
    response = json.loads(requests.get("https://chromestatus.com/data/timeline/featurepopularity?bucket_id=%s"%(bucket)).text)
    for item in response:
        if item["date"] not in data: data[item["date"]] = {}
        data[item["date"]][bucket] = item["day_percentage"]


print("""
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>COOP: same-origin</th>
        <th>COOP: same-origin-allow-popups</th>
        <th>COEP: require-corp</th>
        <th>Cross-Origin Isolated</th>
      </tr>
    </thead>
    <tbody>
""")

for day in data.keys():
    print("<tr><td>%s</td>")
    for bucket in use_counters.values():
        print("<td>%.08f</td>" % (data[day].get(bucket, 0)))
    print("</tr>\n")

print("""
    </tbody>
  </table>
""")
