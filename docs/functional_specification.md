# ParkMatch functional specification

CSE 583, Autumn 2026. ParkMatch is the working name of the project and `parkmatch` the package name; both may still change. The user stories are in `design/user_stories.md`, the use cases in the instructor's template are in `design/use_cases.md`, and the components are in `docs/component_specification.md`. Data facts refer to the snapshot we downloaded on 2026-11-05.

## Background

The National Park System is much bigger than the famous parks. The NPS public API lists 475 units: national parks, monuments, historic sites, historical parks, seashores, recreation areas, memorials, trails and more. They differ a lot; some have dozens of campgrounds and millions of visits a year, others are one building in a city with no entrance fee. Someone choosing a place for a weekend has to read one nps.gov page per park for the description, fees and activities, separate pages for each campground and visitor center, and a separate statistics site (IRMA) to learn how crowded a month is. No single place lets them filter all of that at once.

The 30 user stories in `design/user_stories.md` describe people in that situation. Whatever their interest (hiking, birds, geology, history, stargazing, paddling, a quiet place, a cheap trip), most ask for the same three things: filter the whole system by what matters to them, compare the few parks that survive, and see why a park was suggested instead of getting a bare list. Several also want the tool to say plainly when a fact is unknown, and three stories (James, Linda, Leo) need accessibility information and an interface that works without a mouse or with low vision.

ParkMatch is a small Python package, `parkmatch`, plus a web app we plan to add after the technology review. The user says what they care about (states, activities, topics such as geology or Civil War history, a maximum entrance fee, facilities such as accessible restrooms, whether they need a campground, how busy a park may be and in which months) and the package returns the matching units ranked by a `match_score`, with a `match_reasons` sentence for each. Around that sit a one-park summary, a side-by-side comparison of two or three parks, a 12-month visitation profile, a name search, and a map with a text alternative. The data comes from the National Park Service: the NPS API for park facts and the NPS Visitor Use Statistics for monthly visits since 1979. A third source, Open-Meteo, is planned for monthly temperatures.

In the course's terms the project is mostly a tool: an installable package with a small public API (`load_parks`, `build_park_table`, `find_parks`, `compare_parks`, `park_summary`, `search_parks`), tests, an example script and a data snapshot that installs with it. The Streamlit app on top is closer to an analysis, showing the same tables as filtered views, a map and monthly charts for people who do not write Python. The two sources have different shapes (one row per park against one row per park per month per statistic), and joining them is the data-integration part of the project.

We include all 475 units rather than the 63 national parks alone. A teacher planning a field trip (Lily), a history fan (Amelia), a business traveler with one free afternoon (Lucas) and a city dweller without a car (Grace) are often better served by a historic site or a recreation area near a city than by Yellowstone, and the quiet places Mia wants are more likely to be monuments. The API also makes the narrow choice awkward: only 52 units carry the exact designation "National Park", 35 have a blank designation, and 62 span more than one state. Keeping every unit adds no work in the matcher, and the designation column stays in the table for anyone who wants to narrow the results.

## User profile

We grouped the 30 personas into four visitor types by what they need, plus one maintainer role. None of the visitors writes Python. They browse travel websites, use a map app on their phone and fill in web forms, and that is the computing skill the app assumes. The package itself is for people who can run `pip install` and a few lines of pandas, which in practice means us and the instructors.

### Trip planners choosing a destination

Alex, Sarah, Sophie, Ethan, Lucas, Isabella, Mia and Natalie. They know little about the park system ("national park" means the famous ones, and Sophie does not know U.S. geography) and plenty about shopping for a trip online. They need a few plain filters (state, activity, facilities, fee, how busy), a photo and a short description per park, a reason for each suggestion, and a way to shrink the list to two or three options. Ethan needs an unknown fee labeled unknown rather than zero, Mia needs the quiet months, Lucas needs a one-screen summary, and Natalie wants to stack several filters and share a comparison table with friends.

### Interest-led explorers

Olivia (landscapes), Noah (wildlife), Chloe (birds), Daniel (stargazing), Zoe (deserts and rock formations), Owen (geology), Amelia (history), William (paddling), Ella (cycling), Michael (hard hikes) and Jack (trail running). They know their subject well and the park system badly, and they are comfortable with websites and digital maps. They need the API's activity and topic vocabularies exposed as filters (Astronomy, Night Sky, Birdwatching, Wetlands, Geology, Volcanoes, Kayaking, Road Biking), images for visual browsing, ranked results with reasons, and an honest marker where our data stops. For Michael, Jack and Ella it stops early: we can say a park lists Hiking or Mountain Biking and nothing about distance, elevation or surface. For Zoe there is no "Deserts" topic at all; the closest tags are Dunes, Rock Landscapes and Features, and Canyons and Canyonlands, and the tool should say that is what it searched.

### Logistics-first travelers

David (road trip), Henry (RV), Ryan (first camping trip), Grace (no car), Lily (school group) and, again, Natalie. They plan around a vehicle, a campground, a bus or a group. Most are experienced with navigation apps and trip organizing; Ryan is a beginner who wants facilities described in plain words. They need campground facts (sites, reservable sites, RVs allowed, water, toilets, dump station), the amenity flags that matter to a vehicle or a group (Parking - Bus/RV, Bus/Shuttle Stop, Public Transit, and Scenic Driving as an activity), visitor centers and ranger programs for Lily, and a map that shows where parks sit along a route. The data covers this only in part: the campground record has an RV length limit, and nothing in the API says how to get from a train station to a trailhead.

### Access- and comfort-focused visitors

James (wheelchair user), Linda (gentle activities), Leo (low vision), Benjamin (heat), Ava (winter) and Emily (dog owner). Their choice depends on one specific condition, and a general label is not enough. Computing skill varies most here: Linda has basic skills and little experience with interactive maps, while James and Leo are experienced with digital tools and assistive technology. They need the amenity-level flags the API has (Restroom - Accessible, Wheelchair Accessible, Accessible Sites, Benches/Seating, Audio Description, Tactile Exhibit, Braille, Pets Allowed), a plain-text table as the alternative to every map, keyboard-reachable controls and readable contrast in the app, monthly temperatures once Open-Meteo is in, and a note wherever the data is only a label: "Pets Allowed" says nothing about which trails allow dogs, and the campground `wheelchairAccess` field is prose we can show and cannot filter. Following the lecture's point about the tyranny of numbers, we treat these needs as required in UC1, UC2 and UC4 even though few stories raise them.

### Maintainer

One of us now, and whoever keeps the package alive later. They know Python and git, can get a free NPS API key from api.data.gov and set it as `NPS_API_KEY`, and can download a 72 MB CSV by hand. They need one command to refresh the bundled snapshot, a clear error when the rate limit hits rather than a stack trace, a record of the snapshot date and sources, and tests that run without the network.

| Type | Personas | Main use cases |
|---|---|---|
| Trip planners | Alex, Sarah, Sophie, Ethan, Lucas, Isabella, Mia, Natalie | UC1, UC2, UC3, UC5, UC6 |
| Interest-led explorers | Olivia, Noah, Chloe, Daniel, Zoe, Owen, Amelia, William, Ella, Michael, Jack | UC1, UC2, UC6 |
| Logistics-first travelers | David, Henry, Ryan, Grace, Lily, Natalie | UC1, UC2, UC3, UC4 |
| Access- and comfort-focused visitors | James, Linda, Leo, Benjamin, Ava, Emily | UC1, UC2, UC3, UC4, UC5 |
| Maintainer | the team | UC7 |

## Data sources

Two sources are in hand and one is planned. Everything is keyed by the park code, the four-letter lowercase identifier the NPS API uses (`olym`, `mora`, `grsm`). The visitor statistics carry the same letters in uppercase as `UnitCode`, so `UnitCode.lower() == parkCode` is the join, with a small alias table for the codes that differ.

### NPS API

Published by the National Park Service at developer.nps.gov. Access needs an api.data.gov key, free by email form; the shared `DEMO_KEY` also works but allows 30 requests per hour and was rate-limited on the day we built the snapshot. Every endpoint under `https://developer.nps.gov/api/v1/` returns JSON of the form `{"total", "limit", "start", "data": [...]}`, and `limit=1000` returns a whole table in one call for the five endpoints we use. We downloaded them on 2026-11-05, and the package works from that snapshot, so nobody needs a key to use it.

| Endpoint | Raw file | Rows | Fields we keep |
|---|---|---|---|
| `parks` | `parks.json`, 3.9 MB | 475 units | `parkCode`, `fullName`, `designation`, `states`, `latitude`, `longitude`, `description`, `activities`, `topics`, `entranceFees`, `images`, `weatherInfo`, `url` |
| `campgrounds` | `campgrounds.json`, 4.4 MB | 665 campgrounds in 118 parks | `parkCode`, `name`, coordinates, `campsites.totalSites`, `numberOfSitesReservable`, `accessibility.rvAllowed`, `amenities.potableWater`, `amenities.toilets`, `amenities.dumpStation`, `accessibility.wheelchairAccess` |
| `visitorcenters` | `visitorcenters.json`, 4.1 MB | 714 visitor centers in 397 parks | `parkCode`, `name`, coordinates, `url` |
| `amenities/parksplaces` | `amenities_parksplaces.json`, 9.4 MB | 127 amenity types, 9,359 park-amenity links | amenity `name`, `parks[].parkCode` |
| `feespasses` | `feespasses.json`, 0.9 MB | 475 units | `parkCode`, `isFeeFreePark` |

A park record is one row per unit. `states` is a two-letter code or a comma list ("NC,TN"). `activities` and `topics` are lists of names from controlled vocabularies of 104 and 189 names (Hiking appears in 275 units, Camping in 156, Birdwatching in 207, Geology in 148, Night Sky in 122). `description` is about 300 to 400 characters, `latitude` and `longitude` arrive as strings, `weatherInfo` is free text, and `designation` is blank for 35 units. We keep the first image URL and its alt text.

Fees need care. 119 units list at least one entrance fee row (549 rows, 0 to 300 dollars), but the rows mix ordinary visitors with tour buses, school groups and timed-entry reservations, and a unit with no rows is not necessarily free. So we keep three things: `fee_per_vehicle` and `fee_per_person` from the "Entrance - Private Vehicle" and "Entrance - Per Person" rows; the `isFeeFreePark` flag from the `feespasses` endpoint as `fee_free` (365 units are fee free, 110 are not); and `entrance_fee_min`, the lowest non-zero per-person, per-vehicle or motorcycle fee (107 units), or 0 when the unit is fee free and lists no such row (364 units). That leaves four units whose fee is unknown (Coltsville, Fort Matanzas, Lowell and Thomas Cole): they are not marked fee free and list no ordinary fee row, so the table stores NaN and the app shows "fee information not available". Several stories ask for exactly this, a tool that says what the data does not know, and the fee filter leaves unknown fees out unless the user asks for them.

A campground record carries its amenities as short strings that mix type and season ("Flush Toilets - seasonal", "No Toilets", "Yes - seasonal" for water), site counts as strings, and `rvAllowed` as "0" or "1" (328 campgrounds allow RVs). The amenity endpoint lists, for each of 127 amenity names, the parks that have it. The names are specific enough to filter on and hold most of the accessibility information: Restroom - Accessible (239 parks), Wheelchair Accessible (294), Audio Description (90), Tactile Exhibit (87), Braille (44). We also expect to use Picnic Table, Benches/Seating, Bus/Shuttle Stop, Public Transit, Parking - Bus/RV, Water - Drinking/Potable, Cellular Signal and Pets Allowed (96 parks).

One more endpoint is a planned input: `thingstodo` (3,577 rows, with `duration`, `arePetsPermitted`, `accessibilityInformation`, `season` and `isReservationRequired`), which would give pet and duration information per activity. The client can fetch it; the package must not need it to run.

The API is static reference data, one row per unit (or per campground, visitor center or amenity link), refreshed by NPS continuously; we freeze it into a dated snapshot. Its limits for us are the key and rate limit, the short descriptions, the free-text fields we cannot filter on, and the absence of any trail table (no distances, elevation or difficulty anywhere in the API). The vocabularies have rough edges too: no "Deserts" topic, and two near-duplicate activity names for horse camping.

### NPS Visitor Use Statistics

The "NPS Visitor Use Statistics Data Package, 2025" is published by the National Park Service on its DataStore (reference 2317666, DOI 10.57830/2317666), public domain U.S. government data. We use `Main_Data.csv`, 72 MB, direct URL `https://irma.nps.gov/DataStore/DownloadFile/756959?Reference=2317666`. The package also holds `Main_State_Data.csv` (22 MB, file id 756960) and `NPS_VUStats_Data_2025_metadata.xml` (file id 756961), which defines the statistic codes.

| Column | Type | Content |
|---|---|---|
| `UnitCode` | string | four uppercase letters, 406 distinct units |
| `Year` | integer | 1979 to 2025; 2025 is complete through December |
| `Month` | integer | 1 to 12 |
| `Statistic` | code | TRV, TNRV, TV, TRVH, TNRVH, TH, TOS, CL, CCG, TT, TRVS, TTRV, BC, MISC, NROS |
| `Value` | integer | the count for that unit, month and statistic |

The file has 2,905,440 rows, one per unit per month per statistic: a time series, the opposite shape of the API's one-row-per-park table. We use TRV (Recreation Visits) and, for campers, TOS (Total Overnight Stays). Check values from summing TRV over the 12 months: Great Smoky Mountains 2024 = 12,191,834, matching the 12.19 million NPS press figure; Olympic 2024 = 3,717,267; Mount Rainier 2024 = 1,620,006.

We do not bundle the 72 MB file. The snapshot step reduces it to `visitation_annual.csv` (park code, original unit code, year, recreation visits, overnight stays) and `visitation_monthly.csv` (park code, month, mean recreation visits over 2021 to 2025, and that month's share of the year), which is what UC5 shows.

Lowercasing `UnitCode` matches 391 of the 406 statistics units to an API park code. The 15 that do not match are FOCA, JEFM, JODR, JOFK, KICA, LACH, NACA, NAVC, NCPC, NCPE, OBRI, PERL, PRPA, ROLA and SEQU. Nine of them are units the API counts under another code, and the snapshot maps them by hand (the table is in `SNAPSHOT.md`): SEQU and KICA are Sequoia and Kings Canyon, one unit `seki` in the API, so their visits are summed; ROLA and LACH are the Ross Lake and Lake Chelan recreation areas, which the API folds into the North Cascades page `noca`, so they are summed with NOCA; JEFM is the Thomas Jefferson Memorial (`thje`), NCPE is National Capital Parks-East (`nace`), OBRI is Obed Wild and Scenic River (`obed`), PERL is Pearl Harbor National Memorial (`valr`, a code kept from the site's old name) and PRPA is President's Park (`whho`). The other six (FOCA, JODR, JOFK, NACA, NAVC, NCPC) have no API counterpart and stay unmatched. In the other direction, 82 API units have no visitation record at all (trails, affiliated areas, some memorials). Their visits stay NaN, never 0, and the app says "no visitation record".

The package is dated by year; ours is the 2025 edition, and we do not know when the 2026 edition will appear, so the refresh command takes the CSV path as an argument. The statistics say how many people came and nothing about where in the park or on which days, so "less busy" in UC1 means fewer recreation visits in a year, and the monthly profile is an average over five recent years rather than a forecast.

### Open-Meteo (planned, second sprint)

Seven stories (Sarah, Olivia, Ryan, Daniel, Ava, Benjamin, Zoe) ask how warm or cold a park is in a given month. The NPS API only has the free-text `weatherInfo`, so we plan a third source: the Open-Meteo historical weather API at archive-api.open-meteo.com. It is free, needs no key, allows non-commercial use with CC BY 4.0 attribution, and returns daily values such as `temperature_2m_max` and `temperature_2m_min` for any latitude and longitude from the ERA5 reanalysis, on a grid of about 9 km. We verified it with one call (Yellowstone, January 2024). Nothing is implemented yet.

| Item | Plan |
|---|---|
| Request | park coordinates from `parks.csv`, a year range, daily maximum and minimum temperature |
| Reduction | monthly mean of the daily maximum and minimum, one row per park per month |
| Storage | a local cache folder (`.parkmatch_cache/`) rather than package data, because 475 units mean 475 calls |
| Limit | a 9 km reanalysis cell is not a weather station on a mountain pass; the numbers describe the area and the app will say so |

## Use cases

UC1 to UC6 are visitor tasks and UC7 is the maintainer's. The interaction sequences describe the app, and every step maps to one package function so the same behavior can be tested without a browser. Accessibility is part of UC1, UC2 and UC4 rather than a separate use case.

### UC1 Find parks that match my preferences

Personas: most of them, including Alex, Sarah, Michael, Emily, Linda, James, Olivia, Ryan, Ethan, Noah, Chloe, Daniel, Zoe, Henry, Lily, Owen, Amelia, Jack, Ella, William, Isabella and Natalie.

(a) Objective. Turn what a person cares about into a short ranked list of parks, each with a plain sentence saying why it is there and what it lacks.

(b) Expected interactions.

1. User: picks any of states, activities, topics, a maximum entrance fee, required amenities, a campground requirement, and a visitation range or "less busy". For example: Washington, Hiking and Camping, maximum fee 35 dollars, Restroom - Accessible.
2. System: applies the hard filters (states, fee, campground, visits). Parks with an unknown fee are set aside from a fee-limited search unless the user ticks "include parks with unknown fee", and the app will say how many were set aside.
3. System: scores the rest on the soft criteria (activities, topics, amenities). `match_score` is the share of requested soft criteria the park satisfies, from 0 to 1; parks scoring 0 are dropped when any soft criterion was given. The list is sorted by `match_score`, then by recreation visits.
4. System: shows park code, full name, designation, states, `match_score`, `match_reasons`, the fee columns and the latest annual visits. A reason sentence looks like "In WA; offers Hiking and Camping; has Restroom - Accessible; does not list Night Sky; lowest entrance fee $15."
5. User: loosens or adds a filter when the list is empty or too long, then opens one park (UC2), marks two or three for comparison (UC3) or switches to the map (UC4).

Inputs: `states`, `activities`, `topics`, `max_fee`, `amenities`, `needs_campground`, `min_visits`, `max_visits`, `year` (default 2025), `include_unknown_fee` (default false).

Outputs: a table (a pandas DataFrame in the package), one row per matching park, sorted by `match_score` then visits, with `match_score`, `match_reasons` and the park table columns.

### UC2 Look up one park

Personas: Lucas, Alex, Isabella, Amelia, and anyone arriving from UC1 or UC6.

(a) Objective. Show what we know about one unit on one screen, with every unknown labeled as unknown, and point to the official page for the rest.

(b) Expected interactions.

1. User: enters a park code such as `olym`, or clicks a park in a UC1 or UC6 result.
2. System: finds the row; if the code does not exist, it says so and offers the name search (UC6).
3. System: shows full name and designation, states, description, the first image with its alt text, activities and topics, the fee per vehicle and per person or "fee information not available", the number of campgrounds and visitor centers, recreation visits in the latest year, the busiest and quietest months or "no visitation record", and the nps.gov link.
4. User: follows the link for hours, alerts and trails, adds the park to a comparison (UC3), or opens the monthly profile (UC5).

Inputs: one park code (four letters, case does not matter).

Outputs: a dictionary in the package (`park_summary`) and a detail card in the app.

### UC3 Compare two or three parks side by side

Personas: Ethan (cost), Natalie (a group with mixed interests), Benjamin, Mia, Leo and Emily.

(a) Objective. Put the same attributes for two or three parks next to each other, in a table that can be copied and shared.

(b) Expected interactions.

1. User: selects two or three park codes, from UC1 results or by typing them.
2. System: checks the count and the codes, then builds one table with attributes as rows and parks as columns: name, designation, states, lowest entrance fee, fee per vehicle and per person, campgrounds, campgrounds that allow RVs, visitor centers, recreation visits for 2021 to 2025, busiest and quietest month, the nps.gov link, the number of listed activities, and yes or no for five amenities (Restroom - Accessible, Wheelchair Accessible, Water - Drinking/Potable, Pets Allowed, Public Transit).
3. User: swaps one park for another, or copies the table as text or CSV.

Inputs: two or more park codes (the app will cap the pick at three).

Outputs: a DataFrame with attributes as rows and park codes as columns (`compare_parks`).

### UC4 See parks on a map and pick by location

Personas: David, Sophie, Alex, Grace, Lucas, Henry, and Leo for the text alternative.

(a) Objective. Show where parks are (all of them, one state or region, or the UC1 result set) so a person can choose by geography, with a plain table of the same parks for anyone who cannot use the map.

(b) Expected interactions.

1. User: opens the map view, optionally after a UC1 search or with a state filter.
2. System: draws one marker per park at the API coordinates, with a popup showing full name, designation, states, fee or "not available", recreation visits in the latest year, and the link. When a UC1 result exists, only those parks are drawn.
3. User: zooms to the region of a planned route and clicks markers.
4. System: lists the same parks below the map in a plain table sorted by state and name, with the popup fields as columns. This is the text alternative for screen readers and low-vision users, and it is always rendered.
5. User: picks a park code from a popup or the table and opens UC2.

Inputs: an optional list of states and an optional park table (default: all 475 units).

Outputs: a map object from the library chosen at the technology review on 2026-11-17 (candidates: folium, plotly, pydeck) and a DataFrame of the same parks (`parks_as_table`).

### UC5 Check how busy a park is by month (and later how warm)

Personas: Mia, Daniel, Ava, Benjamin, Ryan, Sarah, Zoe and Olivia.

(a) Objective. Tell a visitor which months are busy and quiet at one park, and in the second sprint show typical temperatures next to them.

(b) Expected interactions.

1. User: enters a park code.
2. System: returns a 12-month profile (mean recreation visits over 2021 to 2025 and each month's share of the year) and names the busiest and quietest months. In the app this is a bar chart with the numbers in a table underneath. For one of the 82 units without a visitation record, it says so instead of showing zeros.
3. User (second sprint): asks for temperatures.
4. System (second sprint): fetches, or reads from the cache, the monthly mean of daily maximum and minimum temperature at the park's coordinates and shows them beside the visitation bars, noting the 9 km reanalysis grid.

Inputs: one park code; optionally a year window (default 2021 to 2025).

Outputs: a DataFrame with `month`, `mean_recreation_visits` and `share_of_year` (later also temperature columns), plus the two named months.

### UC6 Search a park by name

Personas: anyone who knows "Rainier" or "Smoky" and not the park code; Sophie in particular.

(a) Objective. Find a park code from part of a name.

(b) Expected interactions.

1. User: types some text, such as "rainier".
2. System: matches it against `full_name` and `name`, case-insensitive, as a substring, and returns the matching rows with park code, full name, designation and states. Empty or whitespace text returns an empty table and a short message.
3. User: picks one match and opens UC2.

Inputs: a text string.

Outputs: a DataFrame of matching parks, possibly empty (`search_parks`).

### UC7 Refresh the data snapshot (maintainer)

Persona: the maintainer, the "technician" role from the lecture.

(a) Objective. Rebuild the bundled CSV tables from fresh NPS downloads, record when and where the data came from, and check that nothing broke.

(b) Expected interactions.

1. Maintainer: gets a free key from api.data.gov, sets it as `NPS_API_KEY`, and downloads `Main_Data.csv` from the DataStore URL into a raw folder that is not committed.
2. Maintainer: runs `download_raw` for `parks`, `campgrounds`, `visitorcenters`, `amenities/parksplaces` and `feespasses` (plus `thingstodo` once we use it).
3. System: calls each endpoint with `limit=1000`, pages with `start` when the total is larger, and writes one JSON file per endpoint. On HTTP 429 it stops with a message naming the rate limit instead of retrying.
4. Maintainer: runs `python -m parkmatch.snapshot` with the raw folder, the visitation CSV and the output folder (`src/parkmatch/data/`) as arguments.
5. System: builds `parks.csv`, `campgrounds.csv`, `visitor_centers.csv`, `amenities.csv`, `visitation_annual.csv` and `visitation_monthly.csv`, applies the alias table, keeps unknown fees and missing visitation as NaN, and writes `SNAPSHOT.md` with the date, source URLs and DOI, the alias table, row counts and the rebuild command.
6. Maintainer: runs `pytest`, compares the row counts with the previous snapshot (475 parks, 400 of the 406 statistics units matched), and commits.

Inputs: the API key (environment variable), the raw folder, the path to `Main_Data.csv`, and the output folder.

Outputs: the raw JSON files, six CSV tables under about 2 MB in total, and `SNAPSHOT.md`.

## Scope and limits

This quarter we build the package `parkmatch`: the data layer (the 2026-11-05 snapshot and its loaders), the matcher (`find_parks`, `explain_match`, `compare_parks`, `search_parks`, `park_summary`), the snapshot builder and the API client, tests that never touch the network, continuous integration with ruff and pytest, and an example script. After the technology review on 2026-11-17 we plan to add the map module, and after that the Streamlit app that exposes UC1 to UC6 to people who do not write Python. Open-Meteo and the `thingstodo` endpoint are second-sprint work and may slip past the final presentation on 2026-12-16.

Trail-level data is the biggest thing we leave out. About half of the user stories ask for trail distance, elevation gain, difficulty or surface, and the NPS API has no trail table; a later version could bring in OpenStreetMap, which is a project of its own. Real-time conditions (road closures, current weather, how crowded it is today) would need calls at request time rather than a snapshot, so they are out as well, and so are routing, user accounts, reservations, pet rules per trail and species lists. Where a story asks for one of these, the app should point to the official nps.gov page rather than guess.

The main risks we see:

- API key and rate limit. `DEMO_KEY` allows 30 requests per hour and was rate-limited on 2026-11-05. The package does not depend on the API at run time, tests fake `requests.get`, and the key is read from an environment variable so it never lands in the repo. The refresh stays a maintainer task that may need a personal key and some patience.
- Data quality in free-text fields. Descriptions are 300 to 400 characters, `weatherInfo` and `wheelchairAccess` are prose, campground amenity strings mix type and season, 35 designations are blank, 4 units have an unknown fee, 82 have no visitation record, and the vocabularies have gaps (no "Deserts" topic) and near-duplicates (two horse camping names). Our rule is to filter only on controlled fields, keep NaN where the data is silent, and write `match_reasons` only from fields we have.
- The map library choice. folium, plotly and pydeck differ in dependencies, in how they render inside Streamlit, and in how easy it is to keep a text table beside the map. We decide at the technology review and keep the map behind one function, `park_map`, so the rest of the package does not change with the choice.

A smaller risk is the calendar: four people, six weeks, and the deadlines for the use cases, the components and the package all fall inside it. We are keeping the component count low on purpose.
