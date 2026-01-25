# -*- coding: utf-8 -*-
"""
Location configuration: State-level locations for JobSpy scraper
Using state-level keywords to reduce duplicates and improve efficiency
Indeed's search is broad, so using states instead of cities reduces redundancy
"""

# Search location list organized by region/country
# Using state-level locations for US, and major regions for international locations
LOCATIONS_BY_REGION = {
    # ========== United States ==========
    "United States": {
        # Nationwide (search first)
        "United States": ["United States"],
        
        # All 50 US States + DC
        "Alabama": ["Alabama"],
        "Alaska": ["Alaska"],
        "Arizona": ["Arizona"],
        "Arkansas": ["Arkansas"],
        "California": ["California"],
        "Colorado": ["Colorado"],
        "Connecticut": ["Connecticut"],
        "Delaware": ["Delaware"],
        "District of Columbia": ["Washington, DC"],
        "Florida": ["Florida"],
        "Georgia": ["Georgia"],
        "Hawaii": ["Hawaii"],
        "Idaho": ["Idaho"],
        "Illinois": ["Illinois"],
        "Indiana": ["Indiana"],
        "Iowa": ["Iowa"],
        "Kansas": ["Kansas"],
        "Kentucky": ["Kentucky"],
        "Louisiana": ["Louisiana"],
        "Maine": ["Maine"],
        "Maryland": ["Maryland"],
        "Massachusetts": ["Massachusetts"],
        "Michigan": ["Michigan"],
        "Minnesota": ["Minnesota"],
        "Mississippi": ["Mississippi"],
        "Missouri": ["Missouri"],
        "Montana": ["Montana"],
        "Nebraska": ["Nebraska"],
        "Nevada": ["Nevada"],
        "New Hampshire": ["New Hampshire"],
        "New Jersey": ["New Jersey"],
        "New Mexico": ["New Mexico"],
        "New York": ["New York"],
        "North Carolina": ["North Carolina"],
        "North Dakota": ["North Dakota"],
        "Ohio": ["Ohio"],
        "Oklahoma": ["Oklahoma"],
        "Oregon": ["Oregon"],
        "Pennsylvania": ["Pennsylvania"],
        "Rhode Island": ["Rhode Island"],
        "South Carolina": ["South Carolina"],
        "South Dakota": ["South Dakota"],
        "Tennessee": ["Tennessee"],
        "Texas": ["Texas"],
        "Utah": ["Utah"],
        "Vermont": ["Vermont"],
        "Virginia": ["Virginia"],
        "Washington": ["Washington"],
        "West Virginia": ["West Virginia"],
        "Wisconsin": ["Wisconsin"],
        "Wyoming": ["Wyoming"],
    },
    
    # ========== United Kingdom ==========
    "United Kingdom": {
        # Countries/Regions
        "England": ["England, United Kingdom"],
        "Scotland": ["Scotland, United Kingdom"],
        "Wales": ["Wales, United Kingdom"],
        "Northern Ireland": ["Northern Ireland, United Kingdom"],
        
        # Major Cities - England
        "London": ["London, England, United Kingdom"],
        "Manchester": ["Manchester, England, United Kingdom"],
        "Birmingham": ["Birmingham, England, United Kingdom"],
        "Leeds": ["Leeds, England, United Kingdom"],
        "Liverpool": ["Liverpool, England, United Kingdom"],
        "Sheffield": ["Sheffield, England, United Kingdom"],
        "Bristol": ["Bristol, England, United Kingdom"],
        "Leicester": ["Leicester, England, United Kingdom"],
        "Coventry": ["Coventry, England, United Kingdom"],
        "Nottingham": ["Nottingham, England, United Kingdom"],
        "Newcastle": ["Newcastle upon Tyne, England, United Kingdom"],
        "Southampton": ["Southampton, England, United Kingdom"],
        "Portsmouth": ["Portsmouth, England, United Kingdom"],
        "Brighton": ["Brighton, England, United Kingdom"],
        "Reading": ["Reading, England, United Kingdom"],
        "Northampton": ["Northampton, England, United Kingdom"],
        "Luton": ["Luton, England, United Kingdom"],
        "Bolton": ["Bolton, England, United Kingdom"],
        "Bournemouth": ["Bournemouth, England, United Kingdom"],
        "Norwich": ["Norwich, England, United Kingdom"],
        "Swindon": ["Swindon, England, United Kingdom"],
        "Southend-on-Sea": ["Southend-on-Sea, England, United Kingdom"],
        "Middlesbrough": ["Middlesbrough, England, United Kingdom"],
        "Peterborough": ["Peterborough, England, United Kingdom"],
        "Cambridge": ["Cambridge, England, United Kingdom"],
        "Oxford": ["Oxford, England, United Kingdom"],
        "Ipswich": ["Ipswich, England, United Kingdom"],
        "Slough": ["Slough, England, United Kingdom"],
        "Blackpool": ["Blackpool, England, United Kingdom"],
        "Milton Keynes": ["Milton Keynes, England, United Kingdom"],
        
        # Major Cities - Scotland
        "Edinburgh": ["Edinburgh, Scotland, United Kingdom"],
        "Glasgow": ["Glasgow, Scotland, United Kingdom"],
        "Aberdeen": ["Aberdeen, Scotland, United Kingdom"],
        "Dundee": ["Dundee, Scotland, United Kingdom"],
        "Inverness": ["Inverness, Scotland, United Kingdom"],
        "Perth": ["Perth, Scotland, United Kingdom"],
        "Stirling": ["Stirling, Scotland, United Kingdom"],
        
        # Major Cities - Wales
        "Cardiff": ["Cardiff, Wales, United Kingdom"],
        "Swansea": ["Swansea, Wales, United Kingdom"],
        "Newport": ["Newport, Wales, United Kingdom"],
        "Wrexham": ["Wrexham, Wales, United Kingdom"],
        "Barry": ["Barry, Wales, United Kingdom"],
        
        # Major Cities - Northern Ireland
        "Belfast": ["Belfast, Northern Ireland, United Kingdom"],
        "Derry": ["Derry, Northern Ireland, United Kingdom"],
        "Lisburn": ["Lisburn, Northern Ireland, United Kingdom"],
        "Newry": ["Newry, Northern Ireland, United Kingdom"],
    },
    
    # ========== Australia ==========
    "Australia": {
        # States/Territories
        "New South Wales": ["New South Wales, Australia"],
        "Victoria": ["Victoria, Australia"],
        "Queensland": ["Queensland, Australia"],
        "Western Australia": ["Western Australia, Australia"],
        "South Australia": ["South Australia, Australia"],
        "Tasmania": ["Tasmania, Australia"],
        "Australian Capital Territory": ["Australian Capital Territory, Australia"],
        "Northern Territory": ["Northern Territory, Australia"],
        
        # Major Cities - New South Wales
        "Sydney": ["Sydney, New South Wales, Australia"],
        "Newcastle": ["Newcastle, New South Wales, Australia"],
        "Wollongong": ["Wollongong, New South Wales, Australia"],
        "Albury": ["Albury, New South Wales, Australia"],
        "Wagga Wagga": ["Wagga Wagga, New South Wales, Australia"],
        "Tamworth": ["Tamworth, New South Wales, Australia"],
        "Orange": ["Orange, New South Wales, Australia"],
        "Dubbo": ["Dubbo, New South Wales, Australia"],
        "Nowra": ["Nowra, New South Wales, Australia"],
        "Bathurst": ["Bathurst, New South Wales, Australia"],
        
        # Major Cities - Victoria
        "Melbourne": ["Melbourne, Victoria, Australia"],
        "Geelong": ["Geelong, Victoria, Australia"],
        "Ballarat": ["Ballarat, Victoria, Australia"],
        "Bendigo": ["Bendigo, Victoria, Australia"],
        "Shepparton": ["Shepparton, Victoria, Australia"],
        "Warrnambool": ["Warrnambool, Victoria, Australia"],
        "Latrobe": ["Latrobe, Victoria, Australia"],
        "Traralgon": ["Traralgon, Victoria, Australia"],
        "Mildura": ["Mildura, Victoria, Australia"],
        "Horsham": ["Horsham, Victoria, Australia"],
        
        # Major Cities - Queensland
        "Brisbane": ["Brisbane, Queensland, Australia"],
        "Gold Coast": ["Gold Coast, Queensland, Australia"],
        "Cairns": ["Cairns, Queensland, Australia"],
        "Townsville": ["Townsville, Queensland, Australia"],
        "Toowoomba": ["Toowoomba, Queensland, Australia"],
        "Rockhampton": ["Rockhampton, Queensland, Australia"],
        "Mackay": ["Mackay, Queensland, Australia"],
        "Bundaberg": ["Bundaberg, Queensland, Australia"],
        "Hervey Bay": ["Hervey Bay, Queensland, Australia"],
        "Gladstone": ["Gladstone, Queensland, Australia"],
        "Mount Isa": ["Mount Isa, Queensland, Australia"],
        "Sunshine Coast": ["Sunshine Coast, Queensland, Australia"],
        
        # Major Cities - Western Australia
        "Perth": ["Perth, Western Australia, Australia"],
        "Fremantle": ["Fremantle, Western Australia, Australia"],
        "Bunbury": ["Bunbury, Western Australia, Australia"],
        "Geraldton": ["Geraldton, Western Australia, Australia"],
        "Kalgoorlie": ["Kalgoorlie, Western Australia, Australia"],
        "Albany": ["Albany, Western Australia, Australia"],
        "Broome": ["Broome, Western Australia, Australia"],
        "Mandurah": ["Mandurah, Western Australia, Australia"],
        
        # Major Cities - South Australia
        "Adelaide": ["Adelaide, South Australia, Australia"],
        "Mount Gambier": ["Mount Gambier, South Australia, Australia"],
        "Whyalla": ["Whyalla, South Australia, Australia"],
        "Murray Bridge": ["Murray Bridge, South Australia, Australia"],
        "Port Augusta": ["Port Augusta, South Australia, Australia"],
        "Port Pirie": ["Port Pirie, South Australia, Australia"],
        
        # Major Cities - Tasmania
        "Hobart": ["Hobart, Tasmania, Australia"],
        "Launceston": ["Launceston, Tasmania, Australia"],
        "Devonport": ["Devonport, Tasmania, Australia"],
        "Burnie": ["Burnie, Tasmania, Australia"],
        
        # Major Cities - Australian Capital Territory
        "Canberra": ["Canberra, Australian Capital Territory, Australia"],
        
        # Major Cities - Northern Territory
        "Darwin": ["Darwin, Northern Territory, Australia"],
        "Alice Springs": ["Alice Springs, Northern Territory, Australia"],
        "Palmerston": ["Palmerston, Northern Territory, Australia"],
    },
    
    # ========== Hong Kong ==========
    "Hong Kong": {
        # Regions
        "Hong Kong": ["Hong Kong"],
        "Hong Kong Island": ["Hong Kong Island, Hong Kong"],
        "Kowloon": ["Kowloon, Hong Kong"],
        "New Territories": ["New Territories, Hong Kong"],
        
        # Major Areas - Hong Kong Island
        "Central": ["Central, Hong Kong"],
        "Wan Chai": ["Wan Chai, Hong Kong"],
        "Causeway Bay": ["Causeway Bay, Hong Kong"],
        "Admiralty": ["Admiralty, Hong Kong"],
        "Sheung Wan": ["Sheung Wan, Hong Kong"],
        "North Point": ["North Point, Hong Kong"],
        "Quarry Bay": ["Quarry Bay, Hong Kong"],
        "Chai Wan": ["Chai Wan, Hong Kong"],
        "Aberdeen": ["Aberdeen, Hong Kong"],
        "Stanley": ["Stanley, Hong Kong"],
        
        # Major Areas - Kowloon
        "Tsim Sha Tsui": ["Tsim Sha Tsui, Hong Kong"],
        "Yau Ma Tei": ["Yau Ma Tei, Hong Kong"],
        "Mong Kok": ["Mong Kok, Hong Kong"],
        "Kowloon City": ["Kowloon City, Hong Kong"],
        "Kwun Tong": ["Kwun Tong, Hong Kong"],
        "Sham Shui Po": ["Sham Shui Po, Hong Kong"],
        "Wong Tai Sin": ["Wong Tai Sin, Hong Kong"],
        "Yau Tsim Mong": ["Yau Tsim Mong, Hong Kong"],
        "Kwun Tong District": ["Kwun Tong District, Hong Kong"],
        
        # Major Areas - New Territories
        "Sha Tin": ["Sha Tin, Hong Kong"],
        "Tuen Mun": ["Tuen Mun, Hong Kong"],
        "Yuen Long": ["Yuen Long, Hong Kong"],
        "Tai Po": ["Tai Po, Hong Kong"],
        "Tsuen Wan": ["Tsuen Wan, Hong Kong"],
        "Fanling": ["Fanling, Hong Kong"],
        "Sheung Shui": ["Sheung Shui, Hong Kong"],
        "Ma On Shan": ["Ma On Shan, Hong Kong"],
        "Tin Shui Wai": ["Tin Shui Wai, Hong Kong"],
        "Tung Chung": ["Tung Chung, Hong Kong"],
    },
    
    # ========== Singapore ==========
    "Singapore": {
        # Country/Regions
        "Singapore": ["Singapore"],
        "Central Region": ["Central Region, Singapore"],
        "North Region": ["North Region, Singapore"],
        "East Region": ["East Region, Singapore"],
        "West Region": ["West Region, Singapore"],
        
        # Major Areas - Central Region
        "Central Business District": ["Central Business District, Singapore"],
        "Marina Bay": ["Marina Bay, Singapore"],
        "Orchard": ["Orchard, Singapore"],
        "Raffles Place": ["Raffles Place, Singapore"],
        "Clarke Quay": ["Clarke Quay, Singapore"],
        "Chinatown": ["Chinatown, Singapore"],
        "Little India": ["Little India, Singapore"],
        "Bugis": ["Bugis, Singapore"],
        "Tiong Bahru": ["Tiong Bahru, Singapore"],
        "Queenstown": ["Queenstown, Singapore"],
        "Bishan": ["Bishan, Singapore"],
        "Toa Payoh": ["Toa Payoh, Singapore"],
        "Ang Mo Kio": ["Ang Mo Kio, Singapore"],
        "Serangoon": ["Serangoon, Singapore"],
        "Punggol": ["Punggol, Singapore"],
        
        # Major Areas - East Region
        "Tampines": ["Tampines, Singapore"],
        "Pasir Ris": ["Pasir Ris, Singapore"],
        "Changi": ["Changi, Singapore"],
        "Bedok": ["Bedok, Singapore"],
        "Simei": ["Simei, Singapore"],
        "Eunos": ["Eunos, Singapore"],
        "Kembangan": ["Kembangan, Singapore"],
        "Katong": ["Katong, Singapore"],
        "Marine Parade": ["Marine Parade, Singapore"],
        "Siglap": ["Siglap, Singapore"],
        
        # Major Areas - West Region
        "Jurong": ["Jurong, Singapore"],
        "Jurong East": ["Jurong East, Singapore"],
        "Jurong West": ["Jurong West, Singapore"],
        "Clementi": ["Clementi, Singapore"],
        "Bukit Batok": ["Bukit Batok, Singapore"],
        "Bukit Panjang": ["Bukit Panjang, Singapore"],
        "Choa Chu Kang": ["Choa Chu Kang, Singapore"],
        "Woodlands": ["Woodlands, Singapore"],
        "Sembawang": ["Sembawang, Singapore"],
        "Yishun": ["Yishun, Singapore"],
        "Admiralty": ["Admiralty, Singapore"],
        "Kranji": ["Kranji, Singapore"],
        "Boon Lay": ["Boon Lay, Singapore"],
        "Pioneer": ["Pioneer, Singapore"],
        "Tuas": ["Tuas, Singapore"],
        
        # Major Areas - North Region
        "Sengkang": ["Sengkang, Singapore"],
        "Hougang": ["Hougang, Singapore"],
        "Punggol": ["Punggol, Singapore"],
        "Seletar": ["Seletar, Singapore"],
        "Yio Chu Kang": ["Yio Chu Kang, Singapore"],
        "Loyang": ["Loyang, Singapore"],
    },
}

# Country code mapping for Indeed (from JobSpy documentation)
COUNTRY_CODES = {
    "United States": "usa",
    "United Kingdom": "uk",
    "Australia": "australia",
    "Hong Kong": "hong kong",
    "Singapore": "singapore",
}

# Backward compatibility: flatten US locations for old code
LOCATIONS_BY_STATE = LOCATIONS_BY_REGION.get("United States", {})

# Expand all locations into a flat list (for backward compatibility)
LOCATIONS = []
for region, states in LOCATIONS_BY_REGION.items():
    for state, locations in states.items():
        LOCATIONS.extend(locations)

