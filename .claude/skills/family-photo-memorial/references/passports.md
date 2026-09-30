# Passports: stamps, itinerary, collage, map, parchment

Old passports are a travel diary: every entry and exit stamp is a dated, placed event, often with the traveller's own notes pencilled beside it. Handled carefully they turn into two strong slides per passport: the passport itself, and a map of where it took her.

## 1. Scan and separate

- Scan the identity page and every page opening that has a stamp or a note. Turn each upright.
- One file per opening in `Separated/`, identity page first:
  `199 - Her first passport - identity page, issued June 7, 1973.jpg`
  `201 - Her first passport - pages 8-9, West Germany, Hungary and East Germany 1977.jpg`
  Put the page numbers and the countries in the name so the family can find a stamp without opening every file.
- Leave out blank pages, but say so in the collage note ("page 6, which is blank, is left out").
- Don't enhance passport pages. The security print is pale by design, and contrast boosting turns it into noise and can make stamps illegible.

## 2. Read every stamp

Go page by page and write down, for each stamp: date, place (port, airport or border crossing), entry or exit, and the country. Copy handwritten notes exactly, in quotation marks, with the original spelling ("MADERA 1973"). Mark anything uncertain with `[?]` or give both readings ("22 June 1973 [or 25]"; "the month could be read as 08"). Never guess a place from a smudge.

Useful things to know:
- A visa has a validity window; the entry stamp, not the visa, dates the visit.
- A border-crossing name (Hegyeshalom, Zahony, Drewitz, Frankfurt (Oder)) tells you the direction of travel as well as the country. Look up what a crossing connected, in that year.
- Use the borders of the time: 1977 has East and West Germany, the USSR and Yugoslavia. Say so on the map.
- A home re-entry stamp ("U.S. Immigration, New York") closes a trip. Unmatched re-entry stamps are worth a line in the note ("three more U.S. return stamps have no matching trip in this passport").
- The identity page gives birthday, birthplace, height, hair and eye colour, issue office and dates, and any "CANCELED" stamp. Issue dates often land on meaningful days (hers was issued on her 47th birthday). Check her age at each trip against her birth date.

## 3. Write the itinerary into the collage note

The `.txt` note for the passport collage holds the whole record, so every other file can just point to it ("see #204 for the full itinerary"):

- the identity page details, transcribed;
- her journeys in date order, grouped into trips with a one-line heading ("Autumn 1977 - across Europe and behind the Iron Curtain");
- one bullet per stamp: date, place, what it shows, her note in quotes;
- what else was happening in her life that year, if the family or the timeline says so ("That autumn followed her 1977 BA from Indiana University").

## 4. The collage slide

Build one collage per passport with `photo_tools.py collage`: identity page first, then the stamped openings in page order, keeping the printed page numbers visible. Use the collage's flat light background (the parchment step relies on it). The caption tells the story in one or two sentences: when it was issued, how old she was, the trips it records.

## 5. The map slide

One map per passport, the slide right after its collage.

- Country outlines from Natural Earth (public domain); label the countries and the period's borders lightly.
- **One continuous journey** (a three-month tour): number the stops in date order, draw curved arrows between them, and put a numbered legend with dates beside the map. Use a dashed line where there are no stamps between two stops, and say in a footnote that the exact route there is unknown.
- **Many separate trips from home** (a decade of holidays): draw each trip from the home town to the destination, one colour per trip, numbered in date order. Say in the footnote that the lines show where she went, not the routes she took.
- Put a far-away trip in an inset rather than shrinking the whole map.
- Place a country's marker at its capital only when the passport doesn't say where, and note that ("'Poland' is marked at Warsaw only to place it on the map").
- Title it in her name ("Barbara's journeys, from her first passport") and keep the map image 16:9 with a flat light background.
- Record in the map's `.txt` where the outlines came from, which lines are dashed and why, and where the generator script lives. Keep the script in the repo, not only in a scratch folder, so the map can be redrawn when the family corrects a date.

## 6. Parchment background

Passports and maps look best "printed" on old paper. Use `scripts/parchment.py`:

1. `parchment.py make parchment.jpg`, then downscale a copy to 1920x1080 for the slide background.
2. `parchment.py blend map.jpg parchment.jpg map-on-parchment.jpg --box L,T,R,B`, where the box is the picture's position on the slide as fractions (for the standard photo slot: `0.1387,0.0533,0.8587,0.7733`). The image's flat background becomes the matching patch of parchment, so it has no visible edge.
3. On those slides: set the parchment as the slide background, remove the picture's drop shadow, and switch caption colours from white/grey to dark ink (title `3B2A1A`, caption `4A3A28`, slide number `6B5A45`).

Blend the whole image, pages included. Masking the pages out to keep them "true" leaves pale halos around the page shadows and ragged, moth-eaten edges; evenly aged pages look intentional and stay perfectly legible.

## 7. Before sharing

Passport pages show a passport number and a machine-readable line. Expired and cancelled passports of someone who has died carry little risk, but ask the family whether the deck will be shared publicly; if so, blur the number on the identity page.
