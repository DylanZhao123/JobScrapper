# -*- coding: utf-8 -*-
"""
Location configuration: organize search locations by state-county order
Systematically cover AI jobs across the United States and international locations
"""

# Search location list organized by state/country
# Format: Each state/country contains its main cities, sorted by geography and importance
LOCATIONS_BY_STATE = {
    # Nationwide (search first)
    "United States": ["United States"],
    
    # California (CA) - Most tech centers
    "California": [
        "San Francisco, CA",
        "San Jose, CA",
        "Palo Alto, CA",
        "Mountain View, CA",
        "Los Angeles, CA",
        "San Diego, CA",
        "Irvine, CA",
        "Sacramento, CA",
        "Oakland, CA",
        "Fresno, CA",
        "Long Beach, CA",
        "Santa Clara, CA",
        "Sunnyvale, CA",
        "Santa Monica, CA",
        "Berkeley, CA",
        "Cupertino, CA",
        "Fremont, CA",
        "San Bernardino, CA",
        "Riverside, CA",
        "Stockton, CA",
        "Bakersfield, CA",
        "Anaheim, CA",
        "Santa Ana, CA",
        "Glendale, CA",
        "Huntington Beach, CA",
    ],
    
    # New York (NY)
    "New York": [
        "New York, NY",
        "Buffalo, NY",
        "Rochester, NY",
        "Albany, NY",
        "Syracuse, NY",
        "Yonkers, NY",
        "White Plains, NY",
        "Brooklyn, NY",
        "Queens, NY",
        "Bronx, NY",
        "Staten Island, NY",
        "Utica, NY",
        "Binghamton, NY",
        "Poughkeepsie, NY",
        "Ithaca, NY",
    ],
    
    # Texas (TX)
    "Texas": [
        "Austin, TX",
        "Dallas, TX",
        "Houston, TX",
        "San Antonio, TX",
        "Fort Worth, TX",
        "Plano, TX",
        "Irving, TX",
        "Arlington, TX",
        "Corpus Christi, TX",
        "Laredo, TX",
        "Lubbock, TX",
        "Garland, TX",
        "Amarillo, TX",
        "Brownsville, TX",
        "Grand Prairie, TX",
        "McKinney, TX",
    ],
    
    # Florida (FL)
    "Florida": [
        "Miami, FL",
        "Tampa, FL",
        "Jacksonville, FL",
        "Orlando, FL",
        "Fort Lauderdale, FL",
        "St. Petersburg, FL",
        "Tallahassee, FL",
        "Port St. Lucie, FL",
        "Cape Coral, FL",
        "Pembroke Pines, FL",
    ],
    
    # Washington (WA)
    "Washington": [
        "Seattle, WA",
        "Spokane, WA",
        "Tacoma, WA",
        "Bellevue, WA",
        "Redmond, WA",
        "Vancouver, WA",
        "Everett, WA",
        "Kent, WA",
    ],
    
    # Massachusetts (MA)
    "Massachusetts": [
        "Boston, MA",
        "Cambridge, MA",
        "Worcester, MA",
        "Springfield, MA",
        "Lowell, MA",
        "New Bedford, MA",
        "Brockton, MA",
        "Quincy, MA",
    ],
    
    # Illinois (IL)
    "Illinois": [
        "Chicago, IL",
        "Aurora, IL",
        "Naperville, IL",
        "Peoria, IL",
        "Rockford, IL",
        "Elgin, IL",
        "Joliet, IL",
        "Schaumburg, IL",
    ],
    
    # Pennsylvania (PA)
    "Pennsylvania": [
        "Philadelphia, PA",
        "Pittsburgh, PA",
        "Allentown, PA",
        "Erie, PA",
        "Reading, PA",
        "Scranton, PA",
        "Lancaster, PA",
        "Harrisburg, PA",
    ],
    
    # Ohio (OH)
    "Ohio": [
        "Columbus, OH",
        "Cleveland, OH",
        "Cincinnati, OH",
        "Toledo, OH",
        "Akron, OH",
        "Dayton, OH",
        "Canton, OH",
        "Youngstown, OH",
    ],
    
    # Georgia (GA)
    "Georgia": [
        "Atlanta, GA",
        "Augusta, GA",
        "Savannah, GA",
        "Athens, GA",
        "Macon, GA",
        "Roswell, GA",
        "Sandy Springs, GA",
        "Columbus, GA",
    ],
    
    # North Carolina (NC)
    "North Carolina": [
        "Charlotte, NC",
        "Raleigh, NC",
        "Greensboro, NC",
        "Durham, NC",
        "Winston-Salem, NC",
        "Fayetteville, NC",
        "Cary, NC",
        "Wilmington, NC",
    ],
    
    # Michigan (MI)
    "Michigan": [
        "Detroit, MI",
        "Grand Rapids, MI",
        "Warren, MI",
        "Sterling Heights, MI",
        "Ann Arbor, MI",
        "Lansing, MI",
        "Flint, MI",
        "Dearborn, MI",
    ],
    
    # New Jersey (NJ)
    "New Jersey": [
        "Newark, NJ",
        "Jersey City, NJ",
        "Paterson, NJ",
        "Elizabeth, NJ",
        "Edison, NJ",
        "Woodbridge, NJ",
        "Lakewood, NJ",
        "Toms River, NJ",
    ],
    
    # Virginia (VA)
    "Virginia": [
        "Arlington, VA",
        "Virginia Beach, VA",
        "Norfolk, VA",
        "Richmond, VA",
        "Alexandria, VA",
        "Chesapeake, VA",
        "Newport News, VA",
        "Hampton, VA",
    ],
    
    # Arizona (AZ)
    "Arizona": [
        "Phoenix, AZ",
        "Tucson, AZ",
        "Mesa, AZ",
        "Chandler, AZ",
        "Scottsdale, AZ",
        "Glendale, AZ",
        "Gilbert, AZ",
        "Tempe, AZ",
    ],
    
    # Tennessee (TN)
    "Tennessee": [
        "Nashville, TN",
        "Memphis, TN",
        "Knoxville, TN",
        "Chattanooga, TN",
        "Murfreesboro, TN",
        "Clarksville, TN",
        "Franklin, TN",
        "Jackson, TN",
    ],
    
    # Indiana (IN)
    "Indiana": [
        "Indianapolis, IN",
        "Fort Wayne, IN",
        "Evansville, IN",
        "South Bend, IN",
        "Carmel, IN",
        "Fishers, IN",
        "Bloomington, IN",
        "Hammond, IN",
    ],
    
    # Missouri (MO)
    "Missouri": [
        "St. Louis, MO",
        "Kansas City, MO",
        "Springfield, MO",
        "Columbia, MO",
        "Independence, MO",
        "Lee's Summit, MO",
        "O'Fallon, MO",
        "St. Joseph, MO",
    ],
    
    # Maryland (MD)
    "Maryland": [
        "Baltimore, MD",
        "Frederick, MD",
        "Rockville, MD",
        "Gaithersburg, MD",
        "Bowie, MD",
        "Annapolis, MD",
        "College Park, MD",
        "Bethesda, MD",
    ],
    
    # Wisconsin (WI)
    "Wisconsin": [
        "Milwaukee, WI",
        "Madison, WI",
        "Green Bay, WI",
        "Kenosha, WI",
        "Racine, WI",
        "Appleton, WI",
        "Waukesha, WI",
        "Oshkosh, WI",
    ],
    
    # Colorado (CO)
    "Colorado": [
        "Denver, CO",
        "Colorado Springs, CO",
        "Aurora, CO",
        "Fort Collins, CO",
        "Boulder, CO",
        "Lakewood, CO",
        "Thornton, CO",
        "Arvada, CO",
    ],
    
    # Oregon (OR)
    "Oregon": [
        "Portland, OR",
        "Eugene, OR",
        "Salem, OR",
        "Gresham, OR",
        "Hillsboro, OR",
        "Bend, OR",
        "Medford, OR",
        "Corvallis, OR",
    ],
    
    # Kentucky (KY)
    "Kentucky": [
        "Louisville, KY",
        "Lexington, KY",
        "Bowling Green, KY",
        "Owensboro, KY",
        "Covington, KY",
        "Hopkinsville, KY",
        "Richmond, KY",
        "Florence, KY",
    ],
    
    # Oklahoma (OK)
    "Oklahoma": [
        "Oklahoma City, OK",
        "Tulsa, OK",
        "Norman, OK",
        "Broken Arrow, OK",
        "Lawton, OK",
        "Edmond, OK",
        "Moore, OK",
        "Midwest City, OK",
    ],
    
    # District of Columbia (DC)
    "District of Columbia": [
        "Washington, DC",
    ],
    
    # Utah (UT) - Tech hub
    "Utah": [
        "Salt Lake City, UT",
        "Provo, UT",
        "Ogden, UT",
        "West Valley City, UT",
        "West Jordan, UT",
        "Orem, UT",
        "Sandy, UT",
        "St. George, UT",
    ],
    
    # Nevada (NV)
    "Nevada": [
        "Las Vegas, NV",
        "Reno, NV",
        "Henderson, NV",
        "North Las Vegas, NV",
        "Sparks, NV",
        "Carson City, NV",
    ],
    
    # Minnesota (MN)
    "Minnesota": [
        "Minneapolis, MN",
        "St. Paul, MN",
        "Rochester, MN",
        "Duluth, MN",
        "Bloomington, MN",
        "Brooklyn Park, MN",
        "Plymouth, MN",
        "St. Cloud, MN",
    ],
    
    # Connecticut (CT)
    "Connecticut": [
        "Hartford, CT",
        "Stamford, CT",
        "New Haven, CT",
        "Bridgeport, CT",
        "Waterbury, CT",
        "Norwalk, CT",
        "Danbury, CT",
        "Greenwich, CT",
    ],
    
    # New Hampshire (NH)
    "New Hampshire": [
        "Manchester, NH",
        "Nashua, NH",
        "Concord, NH",
        "Derry, NH",
        "Rochester, NH",
        "Dover, NH",
        "Portsmouth, NH",
    ],
    
    # Rhode Island (RI)
    "Rhode Island": [
        "Providence, RI",
        "Warwick, RI",
        "Cranston, RI",
        "Pawtucket, RI",
        "East Providence, RI",
    ],
    
    # Vermont (VT)
    "Vermont": [
        "Burlington, VT",
        "Essex, VT",
        "South Burlington, VT",
        "Colchester, VT",
        "Montpelier, VT",
    ],
    
    # Maine (ME)
    "Maine": [
        "Portland, ME",
        "Lewiston, ME",
        "Bangor, ME",
        "South Portland, ME",
        "Auburn, ME",
    ],
    
    # Louisiana (LA)
    "Louisiana": [
        "New Orleans, LA",
        "Baton Rouge, LA",
        "Shreveport, LA",
        "Lafayette, LA",
        "Lake Charles, LA",
        "Kenner, LA",
        "Bossier City, LA",
        "Monroe, LA",
    ],
    
    # Alabama (AL)
    "Alabama": [
        "Birmingham, AL",
        "Montgomery, AL",
        "Huntsville, AL",
        "Mobile, AL",
        "Tuscaloosa, AL",
        "Hoover, AL",
        "Dothan, AL",
        "Auburn, AL",
    ],
    
    # Mississippi (MS)
    "Mississippi": [
        "Jackson, MS",
        "Gulfport, MS",
        "Southaven, MS",
        "Hattiesburg, MS",
        "Biloxi, MS",
        "Meridian, MS",
        "Tupelo, MS",
    ],
    
    # Arkansas (AR)
    "Arkansas": [
        "Little Rock, AR",
        "Fayetteville, AR",
        "Fort Smith, AR",
        "Jonesboro, AR",
        "North Little Rock, AR",
        "Conway, AR",
        "Rogers, AR",
        "Pine Bluff, AR",
    ],
    
    # Kansas (KS)
    "Kansas": [
        "Wichita, KS",
        "Overland Park, KS",
        "Kansas City, KS",
        "Olathe, KS",
        "Topeka, KS",
        "Lawrence, KS",
        "Shawnee, KS",
        "Manhattan, KS",
    ],
    
    # Nebraska (NE)
    "Nebraska": [
        "Omaha, NE",
        "Lincoln, NE",
        "Bellevue, NE",
        "Grand Island, NE",
        "Kearney, NE",
        "Fremont, NE",
        "Hastings, NE",
    ],
    
    # Iowa (IA)
    "Iowa": [
        "Des Moines, IA",
        "Cedar Rapids, IA",
        "Davenport, IA",
        "Sioux City, IA",
        "Iowa City, IA",
        "Waterloo, IA",
        "Council Bluffs, IA",
        "Ames, IA",
    ],
    
    # South Dakota (SD)
    "South Dakota": [
        "Sioux Falls, SD",
        "Rapid City, SD",
        "Aberdeen, SD",
        "Brookings, SD",
        "Watertown, SD",
    ],
    
    # North Dakota (ND)
    "North Dakota": [
        "Fargo, ND",
        "Bismarck, ND",
        "Grand Forks, ND",
        "Minot, ND",
        "West Fargo, ND",
    ],
    
    # Montana (MT)
    "Montana": [
        "Billings, MT",
        "Missoula, MT",
        "Great Falls, MT",
        "Bozeman, MT",
        "Butte, MT",
    ],
    
    # Wyoming (WY)
    "Wyoming": [
        "Cheyenne, WY",
        "Casper, WY",
        "Laramie, WY",
        "Gillette, WY",
        "Rock Springs, WY",
    ],
    
    # Idaho (ID)
    "Idaho": [
        "Boise, ID",
        "Nampa, ID",
        "Meridian, ID",
        "Idaho Falls, ID",
        "Pocatello, ID",
        "Caldwell, ID",
        "Coeur d'Alene, ID",
    ],
    
    # New Mexico (NM)
    "New Mexico": [
        "Albuquerque, NM",
        "Las Cruces, NM",
        "Rio Rancho, NM",
        "Santa Fe, NM",
        "Roswell, NM",
        "Farmington, NM",
    ],
    
    # Alaska (AK)
    "Alaska": [
        "Anchorage, AK",
        "Fairbanks, AK",
        "Juneau, AK",
        "Wasilla, AK",
        "Sitka, AK",
    ],
    
    # Hawaii (HI)
    "Hawaii": [
        "Honolulu, HI",
        "Hilo, HI",
        "Kailua, HI",
        "Kaneohe, HI",
        "Pearl City, HI",
    ],
    
    # West Virginia (WV)
    "West Virginia": [
        "Charleston, WV",
        "Huntington, WV",
        "Parkersburg, WV",
        "Morgantown, WV",
        "Wheeling, WV",
    ],
    
    # Delaware (DE)
    "Delaware": [
        "Wilmington, DE",
        "Dover, DE",
        "Newark, DE",
        "Middletown, DE",
        "Smyrna, DE",
    ],
    
    # South Carolina (SC)
    "South Carolina": [
        "Columbia, SC",
        "Charleston, SC",
        "Greenville, SC",
        "North Charleston, SC",
        "Rock Hill, SC",
        "Mount Pleasant, SC",
        "Spartanburg, SC",
        "Sumter, SC",
    ],
    
    # ========== International Locations ==========
    
    # United Kingdom
    "United Kingdom": [
        # England - Major cities
        "London, England, United Kingdom",
        "Manchester, England, United Kingdom",
        "Birmingham, England, United Kingdom",
        "Leeds, England, United Kingdom",
        "Liverpool, England, United Kingdom",
        "Sheffield, England, United Kingdom",
        "Bristol, England, United Kingdom",
        "Leicester, England, United Kingdom",
        "Coventry, England, United Kingdom",
        "Nottingham, England, United Kingdom",
        "Newcastle upon Tyne, England, United Kingdom",
        "Southampton, England, United Kingdom",
        "Portsmouth, England, United Kingdom",
        "Brighton, England, United Kingdom",
        "Reading, England, United Kingdom",
        "Cambridge, England, United Kingdom",
        "Oxford, England, United Kingdom",
        "Bath, England, United Kingdom",
        "York, England, United Kingdom",
        "Norwich, England, United Kingdom",
        "Exeter, England, United Kingdom",
        "Plymouth, England, United Kingdom",
        "Bournemouth, England, United Kingdom",
        "Swindon, England, United Kingdom",
        "Milton Keynes, England, United Kingdom",
        "Peterborough, England, United Kingdom",
        "Ipswich, England, United Kingdom",
        "Colchester, England, United Kingdom",
        "Chelmsford, England, United Kingdom",
        "Guildford, England, United Kingdom",
        # Scotland
        "Edinburgh, Scotland, United Kingdom",
        "Glasgow, Scotland, United Kingdom",
        "Aberdeen, Scotland, United Kingdom",
        "Dundee, Scotland, United Kingdom",
        "Inverness, Scotland, United Kingdom",
        # Wales
        "Cardiff, Wales, United Kingdom",
        "Swansea, Wales, United Kingdom",
        "Newport, Wales, United Kingdom",
        # Northern Ireland
        "Belfast, Northern Ireland, United Kingdom",
    ],
    
    # Canada
    "Canada": [
        # Ontario - Most tech companies
        "Toronto, Ontario, Canada",
        "Ottawa, Ontario, Canada",
        "Mississauga, Ontario, Canada",
        "Brampton, Ontario, Canada",
        "Hamilton, Ontario, Canada",
        "London, Ontario, Canada",
        "Markham, Ontario, Canada",
        "Vaughan, Ontario, Canada",
        "Kitchener, Ontario, Canada",
        "Windsor, Ontario, Canada",
        "Richmond Hill, Ontario, Canada",
        "Oakville, Ontario, Canada",
        "Burlington, Ontario, Canada",
        "Oshawa, Ontario, Canada",
        "St. Catharines, Ontario, Canada",
        "Cambridge, Ontario, Canada",
        "Guelph, Ontario, Canada",
        "Waterloo, Ontario, Canada",
        "Thunder Bay, Ontario, Canada",
        "Sudbury, Ontario, Canada",
        # British Columbia
        "Vancouver, British Columbia, Canada",
        "Surrey, British Columbia, Canada",
        "Burnaby, British Columbia, Canada",
        "Richmond, British Columbia, Canada",
        "Coquitlam, British Columbia, Canada",
        "Langley, British Columbia, Canada",
        "Victoria, British Columbia, Canada",
        "Kelowna, British Columbia, Canada",
        "Abbotsford, British Columbia, Canada",
        "Nanaimo, British Columbia, Canada",
        # Quebec
        "Montreal, Quebec, Canada",
        "Quebec City, Quebec, Canada",
        "Laval, Quebec, Canada",
        "Gatineau, Quebec, Canada",
        "Longueuil, Quebec, Canada",
        "Sherbrooke, Quebec, Canada",
        "Saguenay, Quebec, Canada",
        "Trois-Rivieres, Quebec, Canada",
        # Alberta
        "Calgary, Alberta, Canada",
        "Edmonton, Alberta, Canada",
        "Red Deer, Alberta, Canada",
        "Lethbridge, Alberta, Canada",
        "Airdrie, Alberta, Canada",
        "St. Albert, Alberta, Canada",
        # Other provinces
        "Winnipeg, Manitoba, Canada",
        "Saskatoon, Saskatchewan, Canada",
        "Regina, Saskatchewan, Canada",
        "Halifax, Nova Scotia, Canada",
        "St. John's, Newfoundland and Labrador, Canada",
        "Charlottetown, Prince Edward Island, Canada",
        "Fredericton, New Brunswick, Canada",
        "Moncton, New Brunswick, Canada",
        "Whitehorse, Yukon, Canada",
        "Yellowknife, Northwest Territories, Canada",
        "Iqaluit, Nunavut, Canada",
    ],
    
    # Singapore
    "Singapore": [
        "Singapore, Singapore",
    ],
    
    # Hong Kong
    "Hong Kong": [
        "Hong Kong, Hong Kong",
    ],
}

# Expand state-organized locations into a flat list, maintaining state-county order
LOCATIONS = []
for state, locations in LOCATIONS_BY_STATE.items():
    LOCATIONS.extend(locations)
