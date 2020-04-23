import datetime
import json
import requests

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

# Step 1: Load the four JSON files, and merge them into a single data structure:
#
# data[_date_][_bucket_id_] = _value_as_percentage_between_1_and_100;
#
days = set()
data = {}
for bucket in use_counters.values():
    response = json.loads(requests.get("https://chromestatus.com/data/timeline/featurepopularity?bucket_id=%s"%(bucket)).text)
    for item in response:
        days.add(item["date"])
        if item["date"] not in data: data[item["date"]] = {}
        data[item["date"]][bucket] = item["day_percentage"] * 100

#
# Step 2: Build up a JavaScript representation of the last  out the last ~14 entries as a JavaScript array:
#
days_to_render = sorted(days)[-60:]

data_string = """
    const day_labels = %s;
    const bucket_data = {
""" % json.dumps(days_to_render)
for bucket in use_counters.values():
    data_for_bucket = []
    for day in days_to_render:
        data_for_bucket.append(data[day].get(bucket, 0))
    data_string += "      \"%d\": %s,\n" % (bucket, json.dumps(data_for_bucket))
data_string += "    };\n"

#
# Step 3: Render some HTML.
#
print("""<!DOCTYPE html>
<head>
<script src="https://cdn.jsdelivr.net/npm/chart.js@2.8.0"></script>
<link rel="preconnect" href="https://fonts.gstatic.com/" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;800&family=Roboto+Slab:wght@100;500&display=swap" rel="stylesheet">
<style>
  body, html {
    border: 0;
    margin: 0;
    padding: 0;
  }
  h1 {
    background: black;
    color: white;
    font: 100 40px/1.2 'Roboto Slab', sans-serif;
    margin: 0 0 40px 0;
    padding: 40px;
    text-align: right;
  }
  article {
    max-width: 750px;
    margin: 0 auto;
  }
  h2 {
    font: 800 24px/1.2 'Open Sans', sans-serif;
  }
  p, ul {
    font: 18px/1.2 'Open Sans', sans-serif;
  }
  li {
    margin: 0 0 20px 20px;
  }
  footer {
    background: black;
    color: white;
    margin: 0;
    padding: 1ch 2ch;
    font: 15px/1.4 'Open Sans', sans-serif;
    text-align: right;
  }
    footer a, footer a:visited {
      font-family: monospace;
      color: #52cbff;
    }
</style>
</head>
<body>
  <h1>Clever Title Goes Here</h1>
  <article>
    <h2>Content Security Policy</h2>
    <p>
      We believe that a carefully-crafted
      <a href="https://w3c.github.io/webappsec-csp/">Content Security Policy</a>
      can help protect web applications from injection attacks that would otherwise lead to script
      execution. <a href="https://csp.withgoogle.com/docs/strict-csp.html">Strict CSP</a> is a
      reasonable approach, one which we'd like to encourage.
    </p>
    <p>
      The data below is gathered from
      <a href="https://chromestatus.com/metrics/feature/popularity">Chrome's usage statistics</a>,
      and represents the percentage of Chrome page loads that use CSP at all, that define a
      <a href="https://csp.withgoogle.com/docs/strict-csp.html">Strict CSP</a>, and that define
      a Strict<em>er</em> CSP that avoids <code>'strict-dynamic'</code>.
    </p>
      
    <canvas id="csp_usage"></canvas>
  </article>

  <article>
    <h2>Trusted Types</h2>
    <p>
      <a href="https://github.com/w3c/webappsec-trusted-types/">Trusted Types</a> give developers
      the ability to avoid the risks of dumping raw strings into DOM methods and setters that can
      cause script execution.
    </p>
    <p>
      The data below is gathered from
      <a href="https://chromestatus.com/metrics/feature/popularity">Chrome's usage statistics</a>,
      and represents the percentage of Chrome page loads that use Trusted Types in either enforcing
      or reporting mode, and of those, which enforce Trusted Types.
    </p>
      
    <canvas id="tt_usage"></canvas>
  </article>

  <article>
    <h2>Isolation</h2>
    <p>
      <code>Cross-Origin-Opener-Policy</code> and <code>Cross-Origin-Embedder-Policy</code> help
      developers mitigate the risk of <a href="https://meltdownattack.com/">Spectre</a> and similar
      attacks.
    </p>
    <p>
      The data below is gathered from
      <a href="https://chromestatus.com/metrics/feature/popularity">Chrome's usage statistics</a>,
      and represents the percentage of Chrome page loads that use COOP and COEP, and those that
      have opted into cross-origin isolation by using both.
    </p>
      
    <canvas id="coop_coep_usage"></canvas>
  </article>

  <script>
    %s

    const chart_options = {
      scales: {
        yAxes: [
          {
            ticks: {
              beginAtZero: true
            }
          }
        ]
      }
    };

    let csp_chart = new Chart(document.querySelector('#csp_usage').getContext('2d'), {
      type: "line",
      data: {
        labels: day_labels,
        datasets: [
          {
            label: "All CSP",
            borderColor: 'rgb(255,99,132)',
            data: bucket_data["15"]
          },
          {
            label: "Reasonable CSP",
            borderColor: 'blue',
            data: bucket_data["3132"]
          },
          {
            label: "Better than Reasonable CSP",
            borderColor: 'green',
            data: bucket_data["3137"]
          }
        ]
      },
      options: chart_options
    });

    let tt_chart = new Chart(document.querySelector('#tt_usage').getContext('2d'), {
      type: "line",
      data: {
        labels: day_labels,
        datasets: [
          {
            label: "Trusted Types",
            borderColor: 'rgb(255,99,132)',
            data: bucket_data["2722"]
          },
          {
            label: "Enforced",
            borderColor: "green",
            data: bucket_data["3160"]
          }
        ]
      },
      options: chart_options
    });

    let coop_coep_chart = new Chart(document.querySelector('#coop_coep_usage').getContext('2d'), {
      type: "line",
      data: {
        labels: day_labels,
        datasets: [
          {
            label: "COOP: same-origin",
            borderColor: 'rgb(255,99,132)',
            data: bucket_data["3197"]
          },
          {
            label: "COEP: require-corp",
            borderColor: "blue",
            data: bucket_data["3199"]
          },
          {
            label: "Cross-Origin Isolated",
            borderColor: "green",
            data: bucket_data["3200"]
          }
        ]
      },
      options: chart_options
    });
  </script>
  <footer>
    Updated at %s.
  </footer>
</body>
</html>
""" % (data_string, datetime.date.today()))
