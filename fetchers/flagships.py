import re
from datetime import datetime

from requests.help import main

# Hardcoded flagship events that do not appear on aggregator sites
flagship_events = [
    {
        "name": "WeAreDevelopers World Congress",
        "date": "2026-07-08 to 2026-07-10",
        "location": "Berlin, Germany",
        "register": "[↗](https://www.wearedevelopers.com/world-congress)"
    },
    {
        "name": "WeAreDevelopers North America",
        "date": "2026-09-22 to 2026-09-24",
        "location": "San Jose, USA",
        "register": "[↗](https://www.wearedevelopers.com/world-congress-north-america)"
    },
    {
        "name": "WeAreDevelopers India",
        "date": "2026-10-01",
        "location": "Bengaluru, India",
        "register": "[↗](https://www.wearedevelopers.com/conference-india)"
    },
    {
        "name": "DevRelCon NYC",
        "date": "2026-07-22 to 2026-07-23",
        "location": "New York, USA",
        "register": "[↗](https://nyc.devrelcon.dev)"
    },
    {
        "name": "SaaStr Annual",
        "date": "2026-09-09 to 2026-09-11",
        "location": "San Mateo, USA",
        "register": "[↗](https://saastr.com/events)"
    },
    {
        "name": "KubeCon + CloudNativeCon North America",
        "date": "2026-11-09 to 2026-11-12",
        "location": "Salt Lake City, USA",
        "register": "[↗](https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america)"
    },
    {
        "name": "KubeCon + CloudNativeCon Europe",
        "date": "TBA",
        "location": "Barcelona, Spain",
        "register": "[↗](https://events.linuxfoundation.org/kubecon-cloudnativecon-europe)"
    },
    {
        "name": "KubeCon + CloudNativeCon India",
        "date": "2026-06-18 to 2026-06-19",
        "location": "Mumbai, India",
        "register": "[↗](https://events.linuxfoundation.org/kubecon-cloudnativecon-india)"
    },
    {
        "name": "KubeCon + CloudNativeCon Japan",
        "date": "2026-07-28 to 2026-07-30",
        "location": "Yokohama, Japan",
        "register": "[↗](https://events.linuxfoundation.org/kubecon-cloudnativecon-japan)"
    },
    {
        "name": "Open Source Summit North America",
        "date": "TBA",
        "location": "Minneapolis, USA",
        "register": "[↗](https://events.linuxfoundation.org/open-source-summit-north-america)"
    },
    {
        "name": "Open Source Summit Japan",
        "date": "2026-12-01",
        "location": "Tokyo, Japan",
        "register": "[↗](https://events.linuxfoundation.org/open-source-summit-japan)"
    },
    {
        "name": "All Things Open",
        "date": "2026-10-25",
        "location": "Raleigh, USA",
        "register": "[↗](https://allthingsopen.org)"
    },
    {
        "name": "PlatformCon",
        "date": "2026-06-08 to 2026-06-12",
        "location": "Online",
        "register": "[↗](https://platformcon.com)"
    },
    {
        "name": "AWS re:Invent",
        "date": "2026-11-30 to 2026-12-04",
        "location": "Las Vegas, USA",
        "register": "[↗](https://aws.amazon.com/events/reinvent)"
    },
    {
        "name": "Devoxx Belgium",
        "date": "2026-10-05 to 2026-10-09",
        "location": "Antwerp, Belgium",
        "register": "[↗](https://devoxx.be)"
    },
    {
        "name": "Google Cloud Next",
        "date": "TBA",
        "location": "Las Vegas, USA",
        "register": "[↗](https://cloud.withgoogle.com/next)"
    },
    {
        "name": "Microsoft Build",
        "date": "TBA",
        "location": "Seattle, USA",
        "register": "[↗](https://build.microsoft.com/)"
    },
    {
        "name": "NVIDIA GTC",
        "date": "TBA",
        "location": "San Jose, USA",
        "register": "[↗](https://www.nvidia.com/gtc/)"
    },
    {
        "name": "QCon London",
        "date": "TBA",
        "location": "London, UK",
        "register": "[↗](https://qconlondon.com/)"
    },
    {
        "name": "QCon New York",
        "date": "TBA",
        "location": "New York, USA",
        "register": "[↗](https://qconnewyork.com/)"
    },
    {
        "name": "QCon San Francisco",
        "date": "TBA",
        "location": "San Francisco, USA",
        "register": "[↗](https://qconsf.com/)"
    },
    {
        "name": "Web Summit",
        "date": "2026-11-10",
        "location": "Lisbon, Portugal",
        "register": "[↗](https://websummit.com)"
    },
    {
        "name": "GITEX Global",
        "date": "2026-12-07 to 2026-12-11",
        "location": "Dubai, UAE",
        "register": "[↗](https://www.gitex.com)"
    },
    {
        "name": "GITEX AI Europe",
        "date": "2026-06-30 to 2026-07-01",
        "location": "Berlin, Germany",
        "register": "[↗](https://www.gitex.com/gitex-ai-europe)"
    },
    {
        "name": "AIBoomi Events",
        "date": "TBA",
        "location": "Bengaluru, India",
        "register": "[↗](https://saasboomi.org/events)"
    },
    {
        "name": "AIBoomi Annual",
        "date": "TBA",
        "location": "Chennai, India",
        "register": "[↗](https://annual.aiboomi.org)"
    },
    {
        "name": "Cypher AI Conference",
        "date": "2026-10-01 to 2026-10-03",
        "location": "Bengaluru, India",
        "register": "[↗](https://cypher.analyticsindiamag.com)"
    },
    {
        "name": "NASSCOM Tech Events",
        "date": "TBA",
        "location": "India",
        "register": "[↗](https://nasscom.in/events)"
    },
    {
        "name": "DevConf.IN",
        "date": "2026-08-01 to 2026-08-02",
        "location": "Bengaluru, India",
        "register": "[↗](https://www.devconf.info/in)"
    },
    {
        "name": "India SaaS & Marketing Tech Summit",
        "date": "2026-07-15",
        "location": "Bengaluru, India",
        "register": "[↗](https://whysummits.com/india-saas-marketing-tech-summit-2026)"
    },
    {
        "name": "Tech in Asia Events",
        "date": "TBA",
        "location": "Singapore",
        "register": "[↗](https://www.techinasia.com/events)"
    },
    {
        "name": "IDC Asia Pacific Summits",
        "date": "TBA",
        "location": "Singapore",
        "register": "[↗](https://www.idc.com/ap/events)"
    },
    {
        "name": "Stripe Sessions",
        "date": "2027-04-29 to 2027-04-30",
        "location": "San Francisco, USA",
        "register": "[↗](https://stripe.com/sessions)"
    },
    {
        "name": "Datadog DASH",
        "date": "2027-06-09 to 2027-06-10",
        "location": "New York, USA",
        "register": "[↗](https://dash.datadoghq.com)"
    },
    {
        "name": "ObservabilityCON",
        "date": "2026-10-19 to 2026-10-21",
        "location": "Virtual/Online",
        "register": "[↗](https://grafana.com/events/observabilitycon)"
    },
    {
        "name": "GrafanaCON",
        "date": "2027-04-01",
        "location": "Virtual/Online",
        "register": "[↗](https://grafana.com/events/grafanacon)"
    },
    {
        "name": "ObservabilityCON on the Road",
        "date": "TBA",
        "location": "Bengaluru, India",
        "register": "[↗](https://grafana.com/events/observabilitycon-on-the-road/2026/bengaluru)"
    },
    {
        "name": "HashiConf",
        "date": "2026-10-26 to 2026-10-29",
        "location": "Atlanta, USA",
        "register": "[↗](https://www.hashicorp.com/en/conferences/hashiconf)"
    },
    {
        "name": "Twilio SIGNAL",
        "date": "2027-05-06 to 2027-05-07",
        "location": "San Francisco, USA",
        "register": "[↗](https://signal.twilio.com)"
    },
    {
        "name": "Confluent Current",
        "date": "2026-09-23",
        "location": "London, UK",
        "register": "[↗](https://current.confluent.io/london)"
    },
    {
        "name": "MongoDB .local",
        "date": "TBA",
        "location": "Various Cities",
        "register": "[↗](https://www.mongodb.com/events/mongodb-local)"
    },
    {
        "name": "HumanX Europe",
        "date": "2026-09-22 to 2026-09-24",
        "location": "Amsterdam, Netherlands",
        "register": "[↗](https://www.humanx.co/europe)"
    },
    {
        "name": "HumanX US",
        "date": "2027-03-07 to 2027-03-10",
        "location": "Las Vegas, USA",
        "register": "[↗](https://www.humanx.co/us)"
    },
    {
        "name": "AI Engineer Europe",
        "date": "2026-04-08 to 2026-04-10",
        "location": "London, UK",
        "register": "[↗](https://www.ai.engineer/europe/2026)"
    },
    {
        "name": "AI Engineer Miami",
        "date": "2026-04-20",
        "location": "Miami, USA",
        "register": "[↗](https://www.ai.engineer/miami/2026)"
    },
    {
        "name": "AI Engineer Singapore",
        "date": "2026-05-15 to 2026-05-20",
        "location": "Singapore",
        "register": "[↗](https://www.ai.engineer/singapore/2026)"
    },
    {
        "name": "AI Engineer Paris",
        "date": "2026-09-23 to 2026-09-24",
        "location": "Paris, France",
        "register": "[↗](https://www.ai.engineer/paris/2026)"
    },
    {
        "name": "AI Engineer NYC",
        "date": "2026-10-12 to 2026-10-14",
        "location": "New York, USA",
        "register": "[↗](https://www.ai.engineer/nyc/2026)"
    },
    {
        "name": "AI Engineer Shanghai",
        "date": "2026-11-05 to 2026-11-06",
        "location": "Shanghai, China",
        "register": "[↗](https://www.ai.engineer/shanghai/2026)"
    },
    {
        "name": "AI Engineer Code",
        "date": "TBA",
        "location": "Virtual/Online",
        "register": "[↗](https://www.ai.engineer/code/2026)"
    },
    # Indian startup/founder events (added from startupbydoc list, Nov 2026)
    {
        "name": "ScaleOps by TiE Delhi-NCR",
        "date": "2026-11-18",
        "location": "Delhi, India",
        "register": "[↗](https://delhi.tie.org)"
    },
    {
        "name": "Polar Bear Pitching India",
        "date": "2026-11-20",
        "location": "Delhi, India",
        "register": "[↗](https://www.indiasentinels.com/offbeat/no-stage-no-podium-indian-founders-to-pitch-startups-in-an-ice-cold-pool-in-delhi-7691)"
    },
    {
        "name": "StartupLive Mumbai '26",
        "date": "2026-11-20 to 2026-11-21",
        "location": "Mumbai, India",
        "register": "[↗](https://luma.com/h5ca7fjs)"
    },
    {
        "name": "HackPitch",
        "date": "2026-11-20",
        "location": "Kolkata, India",
        "register": "[↗](https://www.startupgrantsindia.com/events)"
    },
    {
        "name": "Agentversity AI Hackathon",
        "date": "2026-11-21",
        "location": "Bengaluru, India",
        "register": "[↗](https://www.startupgrantsindia.com/events)"
    },
    {
        "name": "Entrepreneur AI Summit 2026",
        "date": "2026-11-21",
        "location": "Noida, India",
        "register": "[↗](https://www.entrepreneurindia.com)"
    },
    {
        "name": "The Next Frontier",
        "date": "2026-11-21",
        "location": "Delhi, India",
        "register": "[↗](https://www.startupgrantsindia.com/events)"
    },
    {
        "name": "The Founders × Investors Pitch",
        "date": "2026-11-22",
        "location": "Mumbai, India",
        "register": "[↗](https://www.startupgrantsindia.com/events/the-founders-x-investors-pitch-22nd-november-mumbai)"
    },
    {
        "name": "IVCA Climate Capital Summit",
        "date": "2026-11-26",
        "location": "Mumbai, India",
        "register": "[↗](https://www.ivca.in)"
    },
    {
        "name": "eChai Startup Demo Day",
        "date": "2026-11-28",
        "location": "Pune, India",
        "register": "[↗](https://echai.ventures/events/echai-startup-demo-day-in-pune-nov-28-2026)"
    },
    {
        "name": "Pre-DevFest Founders' Mixer",
        "date": "2026-11-28",
        "location": "Mumbai, India",
        "register": "[↗](https://www.startupgrantsindia.com/events)"
    },
    {
        "name": "Meet The Founder's by Founders Connect",
        "date": "2026-11-29",
        "location": "Delhi, India",
        "register": "[↗](https://www.startupgrantsindia.com/events)"
    },
    {
        "name": "Computer Conversations Buildathon",
        "date": "2026-12-01",
        "location": "Bengaluru, India",
        "register": "[↗](https://www.startupgrantsindia.com/events)"
    },
    {
        "name": "TiEcon Delhi-NCR 2026",
        "date": "2026-12-02 to 2026-12-03",
        "location": "Delhi, India",
        "register": "[↗](https://delhi.tie.org/tiecon-delhi-2026/)"
    },
    {
        "name": "IVCA DII & Exits Forum 2026",
        "date": "2026-12-03",
        "location": "Delhi, India",
        "register": "[↗](https://www.ivca.in)"
    },
    {
        "name": "Entrepreneur's Mixer",
        "date": "2026-12-05",
        "location": "Jaipur, India",
        "register": "[↗](https://www.startupgrantsindia.com/events)"
    },
    {
        "name": "The Founders × Investors Pitch D2C",
        "date": "2026-12-06",
        "location": "Mumbai, India",
        "register": "[↗](https://www.startupgrantsindia.com/events)"
    },
    {
        "name": "Startup Dangal Season 3.0",
        "date": "2026-12-08",
        "location": "Delhi-NCR, India",
        "register": "[↗](https://startupdangal.com/)"
    },
    {
        "name": "Startup Dangal Delhi Roadshow",
        "date": "2026-12-09",
        "location": "Delhi-NCR, India",
        "register": "[↗](https://startupdangal.com/)"
    },
    {
        "name": "South Bengaluru Startups Meetup",
        "date": "2026-12-11",
        "location": "Bengaluru, India",
        "register": "[↗](https://www.startupgrantsindia.com/events)"
    },
]

def determine_region(location):
    loc_lower = location.lower()
    if 'online' in loc_lower or 'virtual' in loc_lower:
        return 'Virtual/Online'
    if any(x in loc_lower for x in ['usa', 'canada', 'united states', 'us']):
        return 'North America'
    if any(x in loc_lower for x in ['uk', 'germany', 'austria', 'france', 'portugal', 'czechia', 'czech republic', 'spain', 'belgium', 'netherlands']):
        return 'Europe'
    if any(x in loc_lower for x in ['india', 'japan', 'china', 'uae', 'singapore']):
        return 'Asia'
    return 'Virtual/Online'

if __name__ == "__main__":
    print(f"Injecting {len(flagship_events)} flagship events into README.md...")
    
    raw_count = len(flagship_events)
    filtered_count = 0
    print(f"[Flagships] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(flagship_events)}")

    import json
    out_file = "events_flagships.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(flagship_events, f, indent=2)
    print(f"Saved {len(flagship_events)} events to {out_file}")

if __name__ == "__main__":
    if "main" in locals() or "main" in globals():
     main()
