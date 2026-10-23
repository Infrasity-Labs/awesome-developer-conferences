"""Country normalization for event locations.

Locations arrive in many shapes ("US", "San Francisco, CA", "Berlin (Germany)",
"London", "United States of America"), so the country is derived with a
best-effort lookup: ISO code / alias / bare city, matched against the last
comma-separated segment first and the whole string second.
"""
import re

# canonical name -> (ISO alpha-2, extra aliases, well-known cities)
COUNTRIES = {
    'United States': ('US', ['usa', 'u.s.a', 'u.s.a.', 'u.s.', 'united states of america', 'america'],
                      ['san francisco', 'new york', 'nyc', 'los angeles', 'chicago', 'seattle', 'austin', 'boston',
                       'orlando', 'miami', 'las vegas', 'salt lake city', 'portland', 'minneapolis', 'phoenix',
                       'raleigh', 'nashville', 'san jose', 'san diego', 'denver', 'atlanta', 'dallas', 'houston',
                       'washington', 'washington dc', 'philadelphia', 'detroit', 'new orleans', 'chicago',
                       'california', 'texas', 'florida', 'palo alto', 'mountain view', 'sunnyvale', 'santa clara']),
    'United Kingdom': ('GB', ['uk', 'u.k.', 'england', 'scotland', 'wales', 'northern ireland', 'great britain'],
                       ['london', 'manchester', 'edinburgh', 'birmingham', 'glasgow', 'bristol', 'cambridge',
                        'oxford', 'leeds', 'belfast', 'cardiff', 'liverpool', 'brighton', 'milton keynes', 'keynes']),
    'Germany': ('DE', ['deutschland'],
                ['berlin', 'munich', 'münchen', 'frankfurt', 'hamburg', 'cologne', 'köln', 'stuttgart', 'dusseldorf',
                 'düsseldorf', 'mainz', 'karlsruhe', 'nuremberg', 'nürnberg', 'leipzig', 'dresden', 'bonn']),
    'France': ('FR', [], ['paris', 'lyon', 'marseille', 'toulouse', 'nice', 'bordeaux', 'nantes', 'lille', 'strasbourg']),
    'Canada': ('CA', [], ['toronto', 'vancouver', 'montreal', 'montréal', 'ottawa', 'calgary', 'edmonton', 'waterloo']),
    'Spain': ('ES', ['españa'], ['madrid', 'barcelona', 'valencia', 'seville', 'sevilla', 'malaga', 'málaga', 'bilbao']),
    'Italy': ('IT', ['italia'], ['rome', 'roma', 'milan', 'milano', 'turin', 'torino', 'bologna', 'florence', 'naples']),
    'Netherlands': ('NL', ['the netherlands', 'holland'], ['amsterdam', 'rotterdam', 'utrecht', 'the hague', 'eindhoven']),
    'Switzerland': ('CH', [], ['zurich', 'zürich', 'geneva', 'basel', 'bern', 'lausanne']),
    'Austria': ('AT', [], ['vienna', 'wien', 'salzburg', 'graz']),
    'Belgium': ('BE', [], ['brussels', 'antwerp', 'ghent', 'leuven']),
    'Sweden': ('SE', [], ['stockholm', 'gothenburg', 'malmö', 'malmo']),
    'Norway': ('NO', [], ['oslo', 'bergen']),
    'Denmark': ('DK', [], ['copenhagen', 'aarhus']),
    'Finland': ('FI', [], ['helsinki', 'tampere', 'espoo']),
    'Ireland': ('IE', [], ['dublin', 'cork', 'galway']),
    'Poland': ('PL', [], ['warsaw', 'krakow', 'kraków', 'wroclaw', 'wrocław', 'gdansk', 'gdańsk', 'poznan']),
    'Portugal': ('PT', [], ['lisbon', 'lisboa', 'porto']),
    'Czechia': ('CZ', ['czech republic'], ['prague', 'praha', 'brno']),
    'Romania': ('RO', [], ['bucharest', 'cluj', 'cluj-napoca']),
    'Greece': ('GR', [], ['athens', 'thessaloniki']),
    'Türkiye': ('TR', ['turkey', 'turkiye', 'türkiye'], ['istanbul', 'ankara', 'izmir']),
    'Russia': ('RU', [], ['moscow', 'saint petersburg', 'st. petersburg']),
    'India': ('IN', ['bharat'],
              ['mumbai', 'bengaluru', 'bangalore', 'delhi', 'new delhi', 'gurugram', 'gurgaon', 'noida', 'pune',
               'chennai', 'hyderabad', 'ahmedabad', 'kolkata', 'jaipur', 'kochi']),
    'China': ('CN', ['prc'], ['shanghai', 'beijing', 'shenzhen', 'guangzhou', 'hangzhou', 'chengdu']),
    'Japan': ('JP', [], ['tokyo', 'osaka', 'kyoto', 'yokohama', 'nagoya', 'fukuoka']),
    'South Korea': ('KR', ['korea', 'republic of korea'], ['seoul', 'busan']),
    'Singapore': ('SG', [], []),
    'Taiwan': ('TW', [], ['taipei', 'taichung', 'kaohsiung']),
    'Hong Kong': ('HK', [], []),
    'Indonesia': ('ID', [], ['jakarta', 'bali', 'bandung', 'surabaya', 'yogyakarta']),
    'Malaysia': ('MY', [], ['kuala lumpur', 'penang']),
    'Vietnam': ('VN', ['viet nam'], ['hanoi', 'ho chi minh', 'ho chi minh city', 'da nang']),
    'Thailand': ('TH', [], ['bangkok', 'chiang mai']),
    'Philippines': ('PH', [], ['manila', 'cebu', 'quezon city']),
    'Pakistan': ('PK', [], ['karachi', 'lahore', 'islamabad']),
    'Bangladesh': ('BD', [], ['dhaka']),
    'Israel': ('IL', [], ['tel aviv', 'jerusalem', 'haifa']),
    'United Arab Emirates': ('AE', ['uae'], ['dubai', 'abu dhabi', 'sharjah']),
    'Saudi Arabia': ('SA', ['ksa'], ['riyadh', 'jeddah']),
    'Australia': ('AU', [], ['sydney', 'melbourne', 'brisbane', 'perth', 'canberra', 'adelaide']),
    'New Zealand': ('NZ', [], ['auckland', 'wellington']),
    'Brazil': ('BR', ['brasil'], ['são paulo', 'sao paulo', 'rio de janeiro', 'campinas', 'florianópolis', 'brasília', 'curitiba']),
    'Mexico': ('MX', ['méxico'], ['mexico city', 'guadalajara', 'monterrey', 'cdmx']),
    'Argentina': ('AR', [], ['buenos aires', 'córdoba']),
    'Colombia': ('CO', [], ['bogotá', 'bogota', 'medellín', 'medellin']),
    'Chile': ('CL', [], ['santiago de chile']),
    'Peru': ('PE', ['perú'], ['lima']),
    'Nigeria': ('NG', [], ['lagos', 'abuja', 'ibadan', 'port harcourt']),
    'Kenya': ('KE', [], ['nairobi', 'mombasa', 'nakuru', 'juja', 'eldoret']),
    'South Africa': ('ZA', [], ['johannesburg', 'cape town', 'durban', 'pretoria']),
    'Egypt': ('EG', [], ['cairo', 'alexandria']),
    'Morocco': ('MA', [], ['casablanca', 'rabat', 'kenitra', 'marrakech']),
    'Ghana': ('GH', [], ['accra']),
    'Tunisia': ('TN', [], ['tunis']),
    'Hungary': ('HU', [], ['budapest']),
    'Bulgaria': ('BG', [], ['sofia']),
    'Serbia': ('RS', [], ['belgrade']),
    'Croatia': ('HR', [], ['zagreb', 'split', 'zadar']),
    'Lithuania': ('LT', [], ['vilnius', 'kaunas']),
    'Latvia': ('LV', [], ['riga']),
    'Estonia': ('EE', [], ['tallinn']),
    'Jordan': ('JO', [], ['amman']),
    'Qatar': ('QA', [], ['doha']),
    'Uganda': ('UG', [], ['kampala', 'jinja']),
    'Zambia': ('ZM', [], ['lusaka']),
    'Rwanda': ('RW', [], ['kigali']),
    'Cameroon': ('CM', [], ['yaounde', 'yaoundé', 'douala']),
    'Senegal': ('SN', [], ['dakar']),
    'Nepal': ('NP', [], ['kathmandu']),
    'Sri Lanka': ('LK', [], ['colombo']),
}

# Countries surfaced as quick filters; the rest still resolve but only appear
# when they have events.
BIG_COUNTRIES = [
    'United States', 'United Kingdom', 'Germany', 'India', 'Canada', 'France', 'Singapore', 'Japan',
    'Australia', 'Spain', 'Netherlands', 'Brazil', 'China', 'Italy', 'Mexico', 'Indonesia', 'South Korea',
    'Poland', 'Portugal', 'Switzerland', 'Sweden', 'United Arab Emirates', 'Türkiye', 'Israel', 'Nigeria',
    'Kenya', 'South Africa', 'Egypt', 'Taiwan', 'Philippines', 'Colombia', 'Argentina',
]

_LOOKUP = {}
_CITY_LOOKUP = {}
for _name, (_iso, _aliases, _cities) in COUNTRIES.items():
    for _k in [_name.lower(), _iso.lower(), *_aliases]:
        _LOOKUP[_k] = _name
    for _c in _cities:
        _CITY_LOOKUP[_c] = _name
# Two-letter codes double as US states ("CA" = California or Canada). After a
# city they read as a state; on their own they read as an ISO country code.
_US_STATES = {
    'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga', 'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la',
    'me', 'md', 'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj', 'nm', 'ny', 'nc', 'nd', 'oh', 'ok',
    'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy', 'dc',
}
_VIRTUAL = ('virtual', 'online', 'remote', 'worldwide', 'global', 'unknown', 'tbd', 'hybrid')


def determine_country(location):
    """Return the canonical country name for a location string, or '' if unknown/virtual."""
    loc = (location or '').strip().lower()
    if not loc or any(w in loc for w in _VIRTUAL):
        return ''

    # "CA (USA)" / "Berlin (Germany)": the parenthesised part is the country.
    paren = re.search(r'\(([^)]+)\)\s*$', loc)
    if paren and paren.group(1).strip() in _LOOKUP:
        return _LOOKUP[paren.group(1).strip()]
    loc = re.sub(r'\s*\([^)]*\)', '', loc).strip()

    segments = [s.strip() for s in loc.split(',') if s.strip()]
    if not segments:
        return ''
    last = segments[-1]

    if len(segments) > 1 and last in _US_STATES:
        # "Berlin, DE" is Germany, "Austin, TX" is the US: trust a known
        # non-US city before falling back to the state-code reading.
        prev = _CITY_LOOKUP.get(segments[-2])
        return prev if prev and prev != 'United States' else 'United States'
    if last in _LOOKUP:
        return _LOOKUP[last]
    for seg in segments:
        if seg in _CITY_LOOKUP:
            return _CITY_LOOKUP[seg]
    return ''
