# ============================================================
# INCLUSION KEYWORDS
# ============================================================
keywords = [
    # DEVREL & DEVELOPER MARKETING
    "developer relations", "devrel", "developer advocacy", "developer evangelist",
    "developer experience", "devx", "developer marketing", "developer ecosystem",
    "developer adoption", "developer community", "technical evangelism",
    "developer-first", "developer platform", "api evangelism", "developer portal",
    "community-led growth", "developer productivity", "developer tooling",
    "developer audience", "technical audience", "technical buyer",

    # GTM & B2B SAAS
    "go-to-market", "gtm", "b2b saas", "saas growth", "product-led growth", "plg",
    "revenue operations", "revops", "sales-led growth", "developer-led growth",
    "saas founder", "saas scaling", "arr", "mrr", "churn", "cac", "product marketing",
    "pmm", "demand generation", "abm", "account-based marketing", "saas metrics",
    "gtm strategy", "saas conference", "saas summit",

    # API & DEVTOOL
    "api economy", "api management", "api monetization", "api governance", "api design",
    "api security", "openapi", "developer tools", "devtools", "sdk", "cli tools",
    "platform engineering", "api-first", "integration platform", "api conference",
    "api summit", "rest api", "graphql", "webhook", "api gateway", "microservices",

    # OBSERVABILITY & INFRASTRUCTURE
    "observability", "monitoring", "apm", "distributed tracing", "logging", "metrics",
    "cloud-native", "kubernetes", "devops", "devsecops", "sre", "site reliability",
    "infrastructure saas", "platform engineering", "cloud infrastructure",
    "ci/cd", "continuous delivery", "continuous integration", "gitops",

    # AI AGENTS & EMERGING TECH
    "ai agents", "agentic ai", "agentic systems", "llm", "large language model",
    "generative ai", "ai developer tools", "mcp", "autonomous workflows", "ai-native",
    "agent orchestration", "developer ai", "ai infrastructure", "ai engineering",
    "llm production", "model deployment", "rag", "retrieval augmented generation",
    "context engineering", "ai-assisted development", "coding agents",
    "prompt engineering", "ai coding", "ai observability", "model evaluation",

    # FLAGSHIP & SCALE SIGNALS
    "world congress", "developer summit", "developer conference", "tech expo",
    "engineering leaders", "tech decision makers", "software architects",
    "engineering leadership", "engineering managers", "tech leaders summit",
    "congress pass", "expo hall", "sponsor booth", "masterclass", "keynote",
    "live coding", "speaker lineup", "platform teams", "secure software",
    "software lifecycle", "ai era", "global developer", "world's largest",
    "world's leading", "20+ tracks", "multiple tracks", "expo floor",

    # OPEN SOURCE & COMMUNITY
    "open source", "foss", "community conference", "hackathon", "open source summit",
    "cloud native foundation", "cncf", "apache foundation", "linux foundation",
    "contributor", "maintainer", "community meetup", "developer meetup",

    # SPONSORSHIP & SPEAKING SIGNALS
    "call for papers", "cfp", "call for speakers", "sponsor", "exhibitor",
    "open cfp", "sponsorship", "speaking opportunity", "speaker application",
    "yc startup", "early stage startup", "devtool startup", "technical sponsor",
    "gold sponsor", "platinum sponsor", "community sponsor", "booth sponsor",

    # FORMAT & EVENT-TYPE SIGNALS
    "conference", "summit", "congress", "expo", "symposium", "unconference",
    "workshop", "bootcamp", "tech event",
    "virtual conference", "hybrid conference", "in-person conference",
    "developer week", "developer day", "devday", "devfest", "devcon",
    
    # OLDER FALLBACKS JUST IN CASE
    "tech lead", "software", "programming", "backend", "frontend", "fullstack", 
    "architecture", "java", "javascript", "python", "ruby", "golang", "rust", 
    "react", "vue"
]

def is_event_relevant(event_text):
    """
    Returns True if the event matches keywords.
    """
    event_text = event_text.lower()
    
    # Check keywords
    if not any(kw.lower() in event_text for kw in keywords):
        return False
        
    return True

def parse_date(date_str):
    """
    Parses a date string (including non-ISO formats with month names) 
    into a sortable YYYY-MM-DD format.
    """
    import re
    match = re.search(r'\d{4}-\d{2}-\d{2}', date_str)
    if match:
        return match.group(0)
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "June", "July", "Sept"]
    if any(m in date_str for m in months):
        year_match = re.search(r'\d{4}', date_str)
        year = year_match.group(0) if year_match else "9999"
        
        for i, m in enumerate(months):
            if m in date_str:
                month = (i % 12) + 1
                return f"{year}-{month:02d}-01"
    
    return "9999-99-99"

def determine_region(location):
    if not location:
        return 'Virtual/Online'
    import re
    loc = location.lower()
    
    if 'online' in loc or 'virtual' in loc:
        if ' & online' not in loc and ' and virtual' not in loc:
            return 'Virtual/Online'

    def has_word(words):
        pattern = r'\b(' + '|'.join(re.escape(w) for w in words) + r')\b'
        return bool(re.search(pattern, loc))

    # Africa
    if has_word(['africa', 'nigeria', 'kenya', 'egypt', 'lagos', 'nairobi', 'cairo', 'durban', 'johannesburg']):
        return 'Africa'
        
    # Australia
    if has_word(['australia', 'new zealand', 'sydney', 'melbourne', 'brisbane']):
        return 'Australia'
        
    # South America
    if has_word(['south america', 'latam', 'brazil', 'argentina', 'colombia', 'chile', 'peru', 'são paulo', 'sau paulo', 'buenos aires', 'lima', 'campinas', 'florianópolis']):
        return 'South America'
        
    # Europe
    europe_countries = ['uk', 'united kingdom', 'england', 'germany', 'france', 'spain', 'italy', 'netherlands', 'belgium', 'switzerland', 'austria', 'portugal', 'sweden', 'norway', 'denmark', 'finland', 'ireland', 'poland', 'czechia', 'czech republic', 'luxembourg', 'scotland', 'wales']
    europe_cities = ['london', 'paris', 'berlin', 'munich', 'amsterdam', 'madrid', 'barcelona', 'rome', 'milan', 'vienna', 'zurich', 'geneva', 'brussels', 'lisbon', 'stockholm', 'oslo', 'copenhagen', 'helsinki', 'dublin', 'warsaw', 'prague', 'frankfurt', 'keynes', 'antwerp']
    if has_word(europe_countries + europe_cities):
        return 'Europe'
        
    # North America
    na_countries = ['usa', 'united states', 'canada', 'mexico']
    na_cities = ['san francisco', 'new york', 'nyc', 'los angeles', 'chicago', 'seattle', 'austin', 'boston', 'orlando', 'miami', 'las vegas', 'salt lake city', 'portland', 'toronto', 'vancouver', 'montreal', 'minneapolis', 'phoenix', 'raleigh', 'california', 'texas']
    if has_word(na_countries + na_cities):
        return 'North America'
        
    # Asia
    asia_countries = ['india', 'china', 'japan', 'korea', 'vietnam', 'singapore', 'indonesia', 'malaysia', 'thailand', 'philippines', 'taiwan', 'qatar', 'uae', 'united arab emirates', 'israel', 'saudi arabia']
    asia_cities = ['tokyo', 'seoul', 'shanghai', 'beijing', 'mumbai', 'bengaluru', 'bangalore', 'delhi', 'new delhi', 'gurugram', 'noida', 'pune', 'chennai', 'hyderabad', 'hanoi', 'ho chi minh', 'jakarta', 'kuala lumpur', 'bangkok', 'manila', 'taipei', 'dubai', 'doha', 'tel aviv']
    if has_word(asia_countries + asia_cities):
        return 'Asia'
        
    return 'Virtual/Online'

def deduplicate_events(events):
    import re
    seen = {}
    deduped = []
    
    for ev in events:
        name = ev['name']
        name_clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', name).lower()
        name_clean = re.sub(r'[^a-z0-9]', '', name_clean)
        
        # Use a combination of name, date, and location to avoid deleting different editions of the same conference series
        date_clean = ev.get('date', '').strip().lower()
        loc_clean = ev.get('location', '').strip().lower()
        key = (name_clean, date_clean, loc_clean)
        
        if key not in seen:
            seen[key] = True
            deduped.append(ev)
            
    return deduped


