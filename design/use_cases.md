# Use cases

This is our homework from the November 3 lecture, updated after the November 12 class. We read
the user stories in `user_stories.md` (32 different people), grouped what people ask for into
themes, and wrote four use cases in the template from the slides. Two of the people are named
Daniel, so the table says which one.

## Themes in the user stories

A story counts under a theme when the person clearly asks for that thing, so one story can
count under several themes.

| Theme | Stories | Who | Use case |
|---|---|---|---|
| Filter by activity or interest | 21 | Alex, Sarah, Michael, David, Linda, Olivia, Ryan, Sophie, Noah, Chloe, Daniel (stargazing), Daniel (ranger programs), Ava, Zoe, Lily, Owen, Amelia, Ella, William, Isabella, Natalie | UC1 |
| Trail details (length, elevation, difficulty, surface) | 19 | Alex, Sarah, Michael, Emily, Linda, James, Olivia, Ryan, Sophie, Lucas, Ava, Benjamin, Zoe, Lily, Owen, Jack, Ella, Isabella, Natalie | not this quarter |
| Facilities (restrooms, water, parking, visitor centers) | 18 | Alex, Sarah, David, Linda, James, Ryan, Ethan, Mia, Ava, Benjamin, Zoe, Henry, Lily, Amelia, Jack, William, Isabella, Leo | UC1 |
| Season, weather and crowds | 15 | Sarah, Michael, David, Olivia, Ryan, Noah, Chloe, Daniel (stargazing), Mia, Ava, Benjamin, Zoe, Jack, William, Priya | partly: yearly visits in UC2 and UC3 |
| Comparing parks | 7 | Alex, Emily, Ethan, Mia, Benjamin, Leo, Natalie | UC3 |
| Short introduction, photo and link | 7 | Alex, Sophie, Olivia, Zoe, Owen, Amelia, Natalie | UC2 |
| Campgrounds | 5 | Ryan, Ethan, Daniel (stargazing), Henry, Isabella | UC1 |
| Accessibility | 5 | Linda, James, Noah, Leo, Daniel (ranger programs) | UC1, UC4 |
| Map and location | 4 | Alex, David, Sophie, Leo | UC4 |
| Current alerts, closures and opening hours | 3 | David, Ava, Priya | not this quarter |
| Getting there without a car | 3 | Grace, Linda, James | partly: the "Public Transit" facility in UC1 |
| Entrance fees and cost | 2 | Ethan, Daniel (ranger programs) | UC1 |
| Pets | 1 | Emily | partly: the "Pets Allowed" facility in UC1 |

Most people want to filter parks by what they like to do and by facilities, and then look
closely at a few parks. Trail details come up almost as often, but the NPS data has no trail
information, so we can't cover them this quarter. Accessibility only shows up in five stories.
The lecture warned against dropping a feature just because few stories mention it, so we
treat it as required: accessible facilities work as normal filters, and the map will always
come with a plain table of the same parks. Of the two newest stories, Daniel's ranger programs
fit UC1, since guided tours are one of the NPS activities, and Priya's live alerts are in the
list at the end.

# Use Case: UC1 Find parks that match what I like

### Who is the User?
*   **Persona/Role:** A traveler choosing where to go, for example Ryan (first camping trip) or Natalie (group trip).
*   **Context:** Most of the stories come down to this. People know what they like to do, but not which of the 475 park sites fit.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   Pick states, activities, facilities, a highest entrance fee, and whether they need a campground.
    *   Get a list of parks, best matches first, with a short reason for each one.
*   **Operational Workflows:**
    *   *Standard Operations:* Ryan picks Washington, Hiking and Camping, a fee of $35 or less, and "needs a campground". Olympic, Mount Rainier and North Cascades come out on top, each with a line such as "Has Hiking and Camping; entrance fee $15; 12 campgrounds."
    *   *Edge/Exception Operations:* If nothing matches, the list is empty and the user can loosen a filter. When a fee limit is set, a park whose fee we don't know is left out, so it never shows up as free by mistake.

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** Filters for state, activity, facility, fee and campground; a match score; a reason for each park; accessible facilities as normal filters.
*   **Desires / Experience Preferences:** Few, clearly labeled choices for Alex and Linda, and the option to combine many filters for Natalie.

### What is Their Skill Level?
*   **Technical Proficiency:** Low to medium. They use travel websites and map apps.
*   **Domain Knowledge:** From none (Alex, Sophie) to a lot about one hobby (Chloe, Owen).

# Use Case: UC2 Look up one park

### Who is the User?
*   **Persona/Role:** Someone who has heard of a park and wants the basics, for example Sophie (international visitor) or Amelia (history fan).
*   **Context:** They come from a UC1 result, or they know part of a park's name.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   Search by part of a name, for example "rainier".
    *   See a short summary of the park and follow the link to its official page.
*   **Operational Workflows:**
    *   *Standard Operations:* Sophie types "rainier" and gets Mount Rainier National Park. The summary shows the type of park, the state, a description, a photo, the activities, the entrance fee, the number of campgrounds, last year's visits and the nps.gov link.
    *   *Edge/Exception Operations:* A name that matches nothing gives an empty result. A park with no visitor statistics shows no visit count instead of 0, and a park whose fee we don't know says "entrance fee unknown".

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** Search by name, a one-park summary, and the official link for anything we don't have.
*   **Desires / Experience Preferences:** Plain words and a photo (Sophie, Olivia).

### What is Their Skill Level?
*   **Technical Proficiency:** Low.
*   **Domain Knowledge:** Low about the park system, sometimes high about their own interest.

# Use Case: UC3 Compare parks side by side

### Who is the User?
*   **Persona/Role:** A traveler deciding between a few parks, for example Ethan (on a budget) or Natalie (planning for a group).
*   **Context:** They already have two or three parks in mind, usually from UC1.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   Pick two or three parks.
    *   See their details next to each other in one table.
*   **Operational Workflows:**
    *   *Standard Operations:* Ethan compares Olympic, Mount Rainier and North Cascades and sees the type of park, states, entrance fee, campgrounds, visits and link in one table, one column per park.
    *   *Edge/Exception Operations:* If one of the park codes doesn't exist, the tool says which one, instead of quietly showing fewer parks.

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** The same details for every park, in the same order.
*   **Desires / Experience Preferences:** A short table that Natalie can share with her friends.

### What is Their Skill Level?
*   **Technical Proficiency:** Low to medium.
*   **Domain Knowledge:** Low.

# Use Case: UC4 See parks on a map (planned)

### Who is the User?
*   **Persona/Role:** A traveler who thinks about places first, for example David (road trip) or Sophie (new to U.S. geography), plus Leo, who has low vision.
*   **Context:** We will build this after our technology review on November 17, where we compare map libraries.

###  What Do They Want to Do with the Tool?
*   **Primary Tasks:**
    *   See the parks from UC1, or all parks in a state, as points on a map.
    *   Click a point to open the park's summary (UC2).
*   **Operational Workflows:**
    *   *Standard Operations:* David searches for parks in Utah and Arizona and sees them on a map, so he can plan stops along his route.
    *   *Edge/Exception Operations:* Some parks, such as long trails, cover many states, but the data gives one point for each park, so they show up as a single marker. The same parks are always listed in a plain table under the map for people who can't use the map.

### What Needs and Desires Do They Have for the Tool?
*   **Functional Needs:** One marker per park, a popup with the name and link, and a table version of the map.
*   **Desires / Experience Preferences:** State names on the map for Sophie; readable text and keyboard access for Leo.

### What is Their Skill Level?
*   **Technical Proficiency:** Low to medium. David uses navigation apps every day; Linda and Alex don't use interactive maps much.
*   **Domain Knowledge:** Low.

## What we can't do this quarter

- **Trail details.** The NPS API has no trail table. This would need another source, such as OpenStreetMap.
- **Weather and season.** Several stories ask about temperatures by month. We might add a weather source later if we have time.
- **Real-time conditions.** Priya wants current alerts, road closures and opening hours. The NPS API has an alerts endpoint, but our package works from a saved copy of the data, so this would mean calling the API with a key every time someone searches. How crowded a park is today isn't in our data either, since our visits are yearly totals.
- **Pet rules for each trail.** We only know whether a park lists "Pets Allowed" as a facility.
