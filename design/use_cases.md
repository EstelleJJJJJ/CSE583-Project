# Use cases for ParkMatch

This file turns the 30 persona stories in `design/user_stories.md` into themes and use cases, which is the homework from the November 3 lecture (slides 44 and 53), due Tuesday, November 10. We tagged the concrete needs each story names, counted how many stories ask for each one, and wrote one use case per cluster of tasks in the slide-53 template. The names UC1 through UC7 are the ones the functional and component specifications in `docs/` use, so renaming one here means changing those files too. ParkMatch is a working name until the team picks one.

## Themes in the user stories

A story counts once for a theme when it names a concrete need in that area; preferences about tone or layout ("prefers simple labels") are not counted. Rows are ordered by how many stories ask, the ranking slide 44 asks for.

| Theme | Stories that ask for it (count) | Persona names | Covered by |
|---|---|---|---|
| Filtering by activity or interest (an NPS activity or topic) | 20 | Alex, Sarah, Michael, David, Linda, Olivia, Ryan, Sophie, Noah, Chloe, Daniel, Ava, Zoe, Lily, Owen, Amelia, Ella, William, Isabella, Natalie | UC1; 104 activity and 189 topic names from the API |
| Trail-level detail (distance, elevation, difficulty, surface, duration) | 19 | Alex, Sarah, Michael, Emily, Linda, James, Olivia, Ryan, Sophie, Lucas, Ava, Benjamin, Zoe, Lily, Owen, Jack, Ella, Isabella, Natalie | Not this quarter; the NPS API has no trail table |
| Facilities and amenities (restrooms, water, picnic areas, parking, visitor centers, benches, launches, cell signal) | 18 | Alex, Sarah, David, Linda, James, Ryan, Ethan, Mia, Ava, Benjamin, Zoe, Henry, Lily, Amelia, Jack, William, Isabella, Leo | UC1 amenities filter, UC2, UC3; 127 amenity types |
| Crowding, popularity and season (temperature questions are counted in the next row) | 8 | Michael, David, Noah, Chloe, Mia, Ava, Jack, William | UC5 and the visits filter in UC1; conditions and closures are not covered |
| Temperature and weather | 7 | Sarah, Olivia, Ryan, Daniel, Ava, Benjamin, Zoe | UC5 in the second sprint (Open-Meteo); for now only the `weather_info` text in UC2 |
| Comparing parks | 7 | Alex, Emily, Ethan, Mia, Benjamin, Leo, Natalie | UC3 |
| Park summary with photo and official link | 7 | Alex, Sophie, Olivia, Zoe, Owen, Amelia, Natalie | UC2 |
| Campgrounds and overnight (sites, reservations, hookups, camping costs) | 5 | Ryan, Ethan, Daniel, Henry, Isabella | UC1 `needs_campground`, UC2, UC3; 665 campgrounds in 118 units |
| Location and map | 4 | Alex, David, Sophie, Leo (text alternative to the map) | UC4, states filter in UC1 |
| Accessibility (mobility, vision, assistive services, low-effort access) | 4 | Linda, James, Noah (accessible observation areas), Leo | UC1, UC2, UC4 table alternative; essential, see below |
| Transit without a car (public transit, shuttles) | 3 | Grace, Linda (viewpoints by shuttle), James (shuttle access) | UC1 via the Public Transit (65 units) and Bus/Shuttle Stop (45) amenities |
| Cost and fees | 1 | Ethan | UC1 `max_fee`, UC2, UC3; 107 units list a per-person, per-vehicle or motorcycle fee, 364 are fee free, 4 are unknown |
| Pets | 1 | Emily | UC1 via the Pets Allowed amenity (96 units), a park-level flag |

The three biggest themes we can serve, activity and topic filtering, facilities, and a park summary, are exactly what the NPS `parks` and `amenities` endpoints hold, so UC1 and UC2 are the core of the package. The second biggest theme, trail-level detail, is the one we cannot serve, and nineteen stories is too many to wave away, so it heads the future work list. In the season row only Mia asks about crowding itself; the other seven want seasonal conditions, which a monthly visitation history answers only loosely. Cost and pets are single stories, and we build them anyway because the fields exist and add little work. Accessibility is four stories, and only two (James, Leo) describe disability access, so a pure count would push it to the bottom. Slide 44 warns against that, and we agree: accessible amenities are ordinary filters in UC1, UC2 passes image alt text through, UC4 never ships a map without a table, and the web app needs keyboard navigation and readable contrast from its first version.

The seven use cases follow, in the slide-53 template.

# Use Case: UC1 Find parks that match my preferences

### Who is the User?
*   **Persona/Role:** A traveler choosing where to go. Natalie, the group trip organizer, is the lead persona because she stacks the most filters.
*   **Context:** Twenty-two stories feed this use case: Alex, Sarah, Michael, Emily, Linda, James, Olivia, Ryan, Ethan, Noah, Chloe, Daniel, Zoe, Henry, Lily, Owen, Amelia, Jack, Ella, William, Isabella and Natalie. They filter on different things and end at the same question of which of the 475 units fit them.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   Pick any mix of states, activities, topics, a maximum entrance fee, required amenities, "needs a campground", and a visitation range or a "less busy" preference.
    *   Read a ranked table with a `match_score` and a `match_reasons` sentence per park, then adjust and run again.
*   **Operational Workflows:**
    *   *Standard Operations:* Natalie asks for Washington units with Hiking and Scenic Driving and a Picnic Table. The states filter is hard; the two activities and the amenity are soft, so each remaining park scores the share of those three it meets (1.0, 0.67 or 0.33), parks that meet none drop out, and the rest sort by score and then by recreation visits. Each row has `park_code`, `full_name`, `match_score` and a sentence such as "In WA; offers Hiking and Scenic Driving; has Picnic Table."
    *   *Edge/Exception Operations:* An empty result comes with a hint to drop an amenity or add a neighboring state. Only four units (Coltsville, Fort Matanzas, Lowell and Thomas Cole) have an unknown fee: the API marks them neither fee free nor with a per-person or per-vehicle fee. They show "fee information not available", never free, and a fee ceiling leaves them out unless `include_unknown_fee` is on. A unit with no visitation record (82 of 475) is never treated as quiet: it fails a visits filter and its reason says "no visitation record". A multi-state unit such as Great Smoky Mountains (NC,TN) matches either state.

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** The filters above, a score that means the same thing for every park, one plain reason per park, and accessibility amenities (Restroom - Accessible in 239 units, Wheelchair Accessible in 294, Audio Description in 90, Tactile Exhibit in 87) offered as ordinary filters.
*   **Desires / Experience Preferences:** Results that explain themselves (one of our earlier short-form stories asked for exactly this). Alex and Linda want few, clearly labeled controls; Michael and Natalie want to stack many filters.

### What is Their Skill Level?
*   **Technical Proficiency:** Low to Medium. All of them use travel websites; none should need to know what a recommendation algorithm is.
*   **Domain Knowledge:** Wide range. Michael, Jack and Chloe know hiking or birding terms; Alex, Sophie and Isabella are new to national parks and need self-explanatory labels.

# Use Case: UC2 Look up one park

### Who is the User?
*   **Persona/Role:** A visitor reading up on one park before deciding. Alex, the first-time visitor, is the lead persona.
*   **Context:** Alex, Sophie, Olivia, Zoe, Owen, Amelia and Natalie ask for a concise introduction, a photo and the official link; Lucas, with one free afternoon, wants the same page to decide quickly. Most other use cases end here.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   Enter a park code such as `olym`, or a name, and get one summary.
    *   Follow the nps.gov link for anything we do not hold (hours, alerts, reservations).
*   **Operational Workflows:**
    *   *Standard Operations:* `park_summary(table, "olym")` returns the designation, states, NPS description, first image with its alt text, activity and topic lists, entrance fees, counts of campgrounds and visitor centers, recreation visits in the latest year, the busiest and quietest months from the 2021 to 2025 profile, and the official URL. For Olympic that means 3,584,187 recreation visits in 2025, August busiest (about 20 percent of the year) and January quietest.
    *   *Edge/Exception Operations:* An unknown code raises an error that points to UC6. Lowell National Historical Park lists no per-person or per-vehicle fee and is not marked fee free, so its summary says "fee information not available"; North Cascades lists no fee rows either, but the `feespasses` endpoint marks it fee free, so it reads "free entrance". Ala Kahakai National Historic Trail has no visitation record, so that line says "no visitation record". Thirty-five units have a blank designation and four have no description; the summary returns None for those, and the app will print "not listed" rather than an empty string.

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** Every field above as a dictionary the app can render and a person can print; image alt text passed through for screen readers; fee and visitation shown as unknown when they are unknown.
*   **Desires / Experience Preferences:** One screen, plain words. Sophie does not know what a National Historic Site is; a one-line gloss of the designation would help, and we have not decided whether to add one.

### What is Their Skill Level?
*   **Technical Proficiency:** Low.
*   **Domain Knowledge:** Low. Sophie is new to U.S. geography; Amelia and Owen know their subjects and the park system hardly at all.

# Use Case: UC3 Compare two or three parks side by side

### Who is the User?
*   **Persona/Role:** A traveler down to a shortlist. Ethan, the budget-conscious student, is the lead persona.
*   **Context:** Alex, Emily, Ethan, Mia, Benjamin, Leo and Natalie want to compare parks. Ethan compares costs, Natalie needs a table she can paste into a group chat, and Leo needs one his screen reader can walk through.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   Choose two or three park codes, usually from a UC1 result or a UC6 search.
    *   Read one table with attributes as rows and parks as columns, and share it.
*   **Operational Workflows:**
    *   *Standard Operations:* `compare_parks(table, ["olym", "mora", "noca"])` returns a DataFrame with the three parks as columns and a fixed row order: name, designation, states, lowest entrance fee, fee per vehicle, fee per person, number of campgrounds and of campgrounds that allow RVs, number of visitor centers, recreation visits for 2021 to 2025, busiest month, quietest month, the nps.gov link, number of activities, and yes or no for a short list of amenities (Restroom - Accessible, Wheelchair Accessible, Water - Drinking/Potable, Pets Allowed, Public Transit). The fee per vehicle row for that call reads 30.0, 30.0 and blank for North Cascades, which is fee free.
    *   *Edge/Exception Operations:* One bad code fails the whole call with a message naming it, so nobody gets a two-park table by surprise. Fewer than two codes is an error; the package accepts more than three, and the app will cap the pick at three. Unknown values print as "fee information not available" or "no visitation record", never as 0 or an empty cell.

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** Attributes as rows (a screen reader reads "fee per vehicle: 30, 30, not available" as one line), the same row order every time, and a plain-text or CSV export.
*   **Desires / Experience Preferences:** Short. Ethan wants costs near the top; Natalie wants something that survives being pasted into a message.

### What is Their Skill Level?
*   **Technical Proficiency:** Low to Medium.
*   **Domain Knowledge:** Low. The fee rows should say what "per vehicle" covers.

# Use Case: UC4 See parks on a map and pick by location

### Who is the User?
*   **Persona/Role:** A traveler who thinks geographically first. David, the road tripper, is the lead persona; Leo defines the text alternative.
*   **Context:** Alex wants to explore park locations on a map, David wants stops along a route, Sophie needs state references because she does not know U.S. geography, and Leo needs a text-based alternative to any interactive map. The map module is not built this sprint; the library choice (folium, plotly or pydeck) is our technology review topic for 2026-11-17.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   See the UC1 result set, or all 475 units, as markers with a popup summary per park.
    *   Narrow by state, click through to UC2, and read the same list as a plain table.
*   **Operational Workflows:**
    *   *Standard Operations:* `park_map(hits)` draws one marker per park at the API's latitude and longitude, with name, designation, states and official link in the popup. `parks_as_table(hits)` returns the same parks as rows; the app shows it under the map, and for some users it is the only view they will read.
    *   *Edge/Exception Operations:* All 475 units have coordinates today, but a later snapshot might not, so a park without coordinates stays in the table with "no coordinates" and is left off the map. A multi-state unit such as the Appalachian National Scenic Trail (14 states) gets one marker at the point NPS gives, so the popup lists every state. With all 475 units on one map the markers overlap wherever small units sit close together, so a state filter or marker clustering is needed. If the map library fails to load, the table still renders.

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** A marker per park, a popup, a state filter, and a table that holds everything the map shows. In the app, keyboard-reachable controls and enough color contrast (Leo).
*   **Desires / Experience Preferences:** State boundaries and a few city labels for orientation (Sophie); simple labels (Alex); a popup that links to UC2 instead of repeating it.

### What is Their Skill Level?
*   **Technical Proficiency:** Low to Medium. David is good with navigation apps; Linda and Alex have little experience with interactive maps, so the default view should make sense without zooming.
*   **Domain Knowledge:** Low.

# Use Case: UC5 Check how busy a park is by month (and, later, how warm)

### Who is the User?
*   **Persona/Role:** A traveler choosing when to go. Mia, who wants quiet, is the lead persona; Benjamin, who avoids heat, leads the temperature part.
*   **Context:** Mia is the only story that asks about crowding directly. Seven stories ask about temperature (Sarah, Olivia, Ryan, Daniel, Ava, Benjamin, Zoe) and seven about season for other reasons (Michael, David, Noah, Chloe, Ava, Jack, William). The monthly visitation profile answers Mia now; temperature normals from Open-Meteo are planned for the second sprint.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   Pick a park and see its 12-month profile: the share of the year's recreation visits in each month, averaged over 2021 to 2025.
    *   Later, see monthly temperature normals for the same park next to that profile.
*   **Operational Workflows:**
    *   *Standard Operations:* `load_monthly_profile()` filtered to one `park_code` gives 12 rows with `mean_recreation_visits` and `share_of_year`. Mount Rainier peaks in July with about 26 percent of the year's visits and bottoms out in February with about 1 percent; Joshua Tree flips, with March busiest and July quietest. The app can draw a bar chart, and a text line ("busiest month: July, 26 percent") always goes with it.
    *   *Edge/Exception Operations:* The 82 API units without a record get "no visitation record for this park" and no chart. Units that began reporting after 2021 (the Appalachian National Scenic Trail reports from 2025 only) get a mean over the years available, and the output names those years. Reported zeros stay zeros: Isle Royale reports zero recreation visits in five months of 2024, a seasonal closure rather than missing data. IRMA also splits some areas differently from the API: Sequoia and Kings Canyon are SEQU and KICA in IRMA and one unit, `seki`, in the API, so we sum them. North Cascades is three IRMA units (NOCA for the park itself, which had only 16,485 recreation visits in 2024, plus the Ross Lake and Lake Chelan recreation areas as ROLA and LACH); the API's `noca` page covers the whole complex, so we sum those too, which gives 1,018,473 for 2024.

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** The 12 shares, the years behind them, the monthly means, a one-line text summary, and a sentence that says what the number is: recorded visits by month since 1979, which tells you how popular a month is and nothing about today's crowd or road status (short story 24).
*   **Desires / Experience Preferences:** Simple charts and clear labels (Benjamin). Mia wants two parks' profiles next to each other, which UC3 can carry as two extra rows.

### What is Their Skill Level?
*   **Technical Proficiency:** Low.
*   **Domain Knowledge:** None needed. The one idea to explain is "share of the year".

# Use Case: UC6 Search a park by name

### Who is the User?
*   **Persona/Role:** Anyone who knows a name, or part of one. Lucas, who is near a park he has heard of, is the lead persona.
*   **Context:** No persona story is about search by itself, but one of our earlier short-form stories asks for it, and UC2, UC3 and UC5 all take a park code that users never know.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   Type part of a name and get the matching parks with their codes.
    *   Hand a code to UC2, UC3 or UC5.
*   **Operational Workflows:**
    *   *Standard Operations:* `search_parks(table, "rainier")` matches case-insensitively against `full_name` and `name` and returns one row, Mount Rainier National Park (`mora`). "glacier" returns Glacier National Park and Glacier Bay; "canyon" returns 11 units, sorted by name.
    *   *Edge/Exception Operations:* No match returns an empty table with a suggestion to try a shorter string or the states filter in UC1. "national" matches 422 units, so the app pages the result. Official spellings matter: "hawaii" finds nothing because the API writes "Hawaiʻi Volcanoes National Park" with an ʻokina, while "volcano" finds it and two others. We plan to normalize accents and the ʻokina on both sides before comparing; we are not sure yet whether fuzzy matching is worth adding.

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** Partial, case-insensitive matching on both name fields, with the park code and designation in the result so Glacier and Glacier Bay can be told apart.
*   **Desires / Experience Preferences:** Fast and forgiving; Lucas wants an answer on the first try.

### What is Their Skill Level?
*   **Technical Proficiency:** Low.
*   **Domain Knowledge:** Low. Users may know a nickname ("the Smokies") that the official name does not contain, and that is a known gap.

# Use Case: UC7 Refresh the data snapshot

### Who is the User?
*   **Persona/Role:** A team member maintaining the package, the "technician" role from the November 3 slides.
*   **Context:** No persona asks for this; every persona depends on it. The package ships bundled CSV tables built from the NPS API and the NPS Visitor Use Statistics, and someone has to rebuild them when NPS adds a unit or publishes the next year of statistics. Tests and users never touch the network, so this is the only place the live sources are called.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   Download the raw API tables (`parks`, `campgrounds`, `visitorcenters`, `amenities/parksplaces` and `feespasses`; `thingstodo` later) with a personal key, plus the IRMA `Main_Data.csv`.
    *   Run `python -m parkmatch.snapshot` to rebuild the bundled CSVs and write the snapshot date and sources into `SNAPSHOT.md`.
*   **Operational Workflows:**
    *   *Standard Operations:* Set `NPS_API_KEY`, call `download_raw(out_dir, api_key)` (one request per endpoint with `limit=1000`), put the IRMA CSV next to the raw files, run the build and the tests, and check that the data folder stays under about 2 MB. Raw files stay out of git.
    *   *Edge/Exception Operations:* An HTTP 429 stops the download with a message that the key is rate limited; `DEMO_KEY` allows 30 requests per hour and is not enough for a refresh. IRMA codes that match no API park code are listed in the build log so the maintainer can extend the alias table (today nine IRMA codes are mapped by hand, for example SEQU and KICA to `seki`; six IRMA codes have no API match and 82 API units have no IRMA record). A renamed API field makes the build fail on that field name instead of writing an empty column.

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** One rebuild command, a log of what matched and what did not, and the download date, source URLs and the DOI of the statistics package (10.57830/2317666) stored next to the data.
*   **Desires / Experience Preferences:** Boring and repeatable. A diff of the old and new CSVs should show only real changes.

### What is Their Skill Level?
*   **Technical Proficiency:** High. Comfortable with Python, environment variables and git.
*   **Domain Knowledge:** Knows the NPS endpoints, the four-letter park codes, and that IRMA unit codes are uppercase and do not always line up with API codes.

## What we cannot support yet

**Trail-level detail.** Nineteen stories ask for the distance, elevation, difficulty, surface or duration of individual trails. The NPS API has no trail table; the nearest fields are the Hiking activity (275 units), the Trails topic (192) and the Trailhead amenity (236), which say that trails exist and nothing about any one trail. Serving Michael, Jack or James properly needs another source, most likely OpenStreetMap, and a technology review of its own.

**Pet rules per trail.** Emily needs to know where dogs are allowed trail by trail. What we have is the park-level amenity Pets Allowed (96 units), with Pet Waste Disposal (14) and Kennel (4). The `thingstodo` endpoint adds `arePetsPermitted` and `petsDescription` per activity, which we plan to pull into the next snapshot, and even that is coarser than a trail.

**Real-time crowding and road closures.** Mia wants quiet, David and Ava want closure notices. Our visitation numbers are recorded visits by month from 1979 through 2025 (2,905,440 rows, 406 units). They describe how popular each month has been and say nothing about this week. Road status and alerts live on each park's nps.gov page, which is one reason every summary carries the official link.

**Snow and mushroom foraging.** Two ideas from the shared document did not become persona stories: Anna, who wants snow-covered mountains with snow conditions, and a forager who wants to know where edible mushrooms such as matsutake grow. The NPS data has no snow depth and no species-by-park list, and foraging rules are set park by park. Open-Meteo may have snowfall history we could add in the second sprint; we have not checked. Foraging stays out of scope.

## Questions for the team

- Project name. ParkMatch is the working name in these documents and in the package name `parkmatch`; we should settle it before anyone renames the repo.
- Web app. The component list assumes a Streamlit app in `app/streamlit_app.py` after the technology review; if someone prefers another framework, now is the time to say so.
- Map library. The 2026-11-17 technology review compares folium, plotly and pydeck; whichever wins, UC4 ships the table alternative with the map.
- Ownership. Seven components (`nps_api`, `snapshot`, `data`, `matcher`, `maps`, `app`, `climate`) and four people; we need names next to each before the package structure lecture on 2026-11-19.
- Activities in UC1. The use case list says all requested activities must be present, while the matcher design scores them as a share; we lean toward the share with full matches sorted first and want the team to confirm.
- IRMA aliases. We map nine codes by hand (the table is in `SNAPSHOT.md`), including ROLA and LACH into `noca`; six IRMA codes (FOCA, JODR, JOFK, NACA, NAVC, NCPC) still have no API match, and someone should check them against the IRMA unit list.
