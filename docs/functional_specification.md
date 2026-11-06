# Functional specification

## Background

The U.S. National Park System has 475 sites: the well-known national parks, but also
monuments, historic sites, seashores, recreation areas and trails. Each one has its own page
on nps.gov, so finding the few that fit what you like (a state, some activities, certain
facilities, a budget) means opening a lot of pages.

ParkMatch puts the National Park Service's own data into one table and lets people filter
it, look at one park, and compare a few parks side by side. Every result comes with a short
reason, so people can see why a park showed up. Right now it's a small Python package. We
plan to add a map and a simple web page on top of it later in the quarter.

## User profile

Our 30 user stories (`design/user_stories.md`) describe people planning a trip. We see four
groups:

- **First-time and casual visitors** such as Alex, Sophie, Lucas, Mia and Isabella. They know
  little about national parks. They want plain words, a photo, a short description and only
  a few filters.
- **People with a hobby** such as Olivia, Noah, Chloe, Daniel, Owen, Amelia, William, Ella,
  Michael and Jack. They know their activity well and want to filter by it.
- **People planning around logistics** such as Sarah, Ryan, Henry, David, Lily, Ethan,
  Natalie and Grace. They care about campgrounds, facilities, fees and how to get there.
- **People with access needs** such as James, Linda, Leo, Benjamin, Ava and Emily. They need
  specific facilities, such as wheelchair access or accessible restrooms. Leo also needs a
  version of the map that works with a screen reader.

None of them write code. They can use a website, fill in a form and read a map. Until the
web page exists, the package is used from Python, mostly by our team and the instructors.

## Data sources

We use two public data sources from the National Park Service and join them on the park
code, a four-letter code such as `olym` for Olympic National Park.

**1. NPS API** (https://www.nps.gov/subjects/developer/api-documentation.htm). It's free with
a key and returns JSON. We use four endpoints:

| Endpoint | What we take | Rows |
|---|---|---|
| `parks` | name, type of park, states, location, description, photo, activities, entrance fees | 475 parks |
| `campgrounds` | how many campgrounds each park has | 665 campgrounds |
| `amenities/parksplaces` | which facilities each park has, such as "Restroom - Accessible" | 127 kinds of facilities |
| `feespasses` | whether a park is fee free | 475 parks |

This data has one row per park and no time dimension.

**2. NPS Visitor Use Statistics** (data package for 2025, doi:10.57830/2317666). It's a 72 MB
CSV with the columns `UnitCode`, `Year`, `Month`, `Statistic` and `Value`, with one row per
park, month and type of count from 1979 to 2025. We use recreation visits (`TRV`), add the
months up into yearly totals, and keep 2016 to 2025.

The two sources have different shapes: the API is one row per park, while the statistics are
monthly numbers over many years. That's the "different granularity" part of the project.
Most codes match once we lowercase them (`OLYM` becomes `olym`). Nine don't match and we map
them by hand. For example, Sequoia (`SEQU`) and Kings Canyon (`KICA`) are listed as one park
in the API (`seki`), so we add their visits together.

What the data doesn't tell us:

- **Some fees.** Four parks are not marked fee free but list no entrance fee, so we keep
  their fee as unknown (NaN) instead of 0.
- **Some visits.** 82 parks, mostly trails and affiliated areas, have no visitor statistics,
  so their visits are NaN.
- **Trails.** There's no trail table, so no trail length, elevation or difficulty.
- **Today's conditions.** Visits are yearly totals and don't say how crowded a park is now.

A small script turns the downloads into two CSV files that ship with the package, so nobody
needs an API key to use it.

## Use cases

The full use cases, written in the template from the lecture, are in `design/use_cases.md`.
Here is a short version of each.

**UC1 Find parks that match what I like**

(a) Objective: get a short list of parks that fit what the person picked, best matches first.

(b) Interactions:
1. User: picks states, activities, facilities, a highest entrance fee, and whether they need a campground.
2. System: keeps the parks in those states, under that fee, and with a campground if asked.
3. System: scores each park by how many of the chosen activities and facilities it has, leaves out parks with none, and sorts by score and then by visits.
4. System: shows each park with its score and a one-line reason.
5. User: changes a filter, or opens one park (UC2), or compares a few (UC3).

**UC2 Look up one park**

(a) Objective: see the basics of one park and get to its official page.

(b) Interactions:
1. User: types part of a park's name.
2. System: lists the parks whose names contain that text.
3. User: picks one.
4. System: shows its type, states, description, photo, activities, fee, campgrounds, visits and nps.gov link, and says "unknown" where we don't know something.

**UC3 Compare parks side by side**

(a) Objective: decide between two or three parks.

(b) Interactions:
1. User: picks two or three parks.
2. System: shows one table with one column per park and the same details in each row.
3. User: removes or adds a park and compares again.

**UC4 See parks on a map (planned)**

(a) Objective: choose parks by where they are.

(b) Interactions:
1. User: opens the map after a UC1 search or for one state.
2. System: shows one marker per park with a popup, and the same parks in a plain table.
3. User: clicks a marker or a table row to open the park (UC2).
