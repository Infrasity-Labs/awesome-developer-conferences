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
