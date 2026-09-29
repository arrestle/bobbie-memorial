---
name: family-photo-memorial
description: Turn scanned family photo albums into an organized, dated photo timeline and a memorial slideshow (PowerPoint that opens in Google Slides) with large centred photos and captions below. Use this whenever someone is sorting, naming, dating, straightening, restoring or captioning old family photos or album scans; building a memorial, celebration-of-life, funeral, anniversary or birthday slideshow from family pictures; making photo collages of a trip, house or theme; stitching an album page that was too big for the scanner; or organizing a parent's or grandparent's photos into a life timeline, even if they don't say "skill" or "slideshow".
---

# Family photo memorial

Help a family turn boxes of album scans into three things:

1. **One clean file per photo**, cut out of its scan, turned upright, straightened, gently restored, and named with who/what/when.
2. **A timeline folder** that puts copies of the photos in life order, grouped into chapters, with a README linking every photo back to its scan.
3. **A slideshow** (`.pptx`, also opens in Google Slides): title slide, one divider per chapter, one large centred photo per slide with the date, title and caption underneath, and a closing slide.

This is emotional work for the family, usually done in a hurry before a memorial. Keep momentum: act on each message, show the result, and let them correct you. Don't make them answer questions they didn't need to.

## Folder layout

Set this up next to the scans (ask where they are if it isn't obvious):

```
Photos/
  scans/        raw scans and phone photos exactly as received - never edit these
  Separated/    NN - Title.jpg  +  NN - Title.txt  (one per photo, originals)
  Enhanced/     same file names, restored copies (the family may delete ones they dislike)
  Timeline/     generated: chapter folders + README.md - rebuilt, never hand-edited
  <Name> - A Life in Photographs.pptx
```

Why this shape: the scans are the only thing that can't be recreated, so nothing touches them. Every other folder can be regenerated, which makes corrections cheap - and there will be dozens of corrections.

**Keep one master list** (a small Python/JSON file in a scratch area) with a row per photo: chapter, sort key, date label, how the date was known, photo number, caption. Generate the Timeline folder, the README and the slideshow from that list every time. When the family renames, re-dates, moves or removes a photo, change the list and rebuild. Never patch the generated outputs by hand - the next rebuild would silently undo it.

## Working through a scan

For each scan the family sends:

1. **Look at it.** Count the photos, note which way each one faces (album pages are often scanned upside down or sideways), and read any handwriting, date stamps or printed captions.
2. **Cut out each photo** and turn it upright. Show a contact sheet of the crops before saving if there are several.
3. **Straighten** anything tilted more than ~0.5°. Measure the angle from the print's edges (see `scripts/photo_tools.py measure-tilt`); if the edges disagree (hand-trimmed prints often aren't square), use a grid overlay and your eyes. After rotating, trim the wedge-shaped corners so no background shows.
4. **Enhance** into `Enhanced/` (see below).
5. **Name it** `NN - Title.jpg`, using the next free number, and write `NN - Title.txt` with: source scan, any caption text copied exactly, date stamps, and who told you what ("Family recollection (Andrea): ...").
6. **Add a row** to the master list, rebuild, validate, and report the slide number it landed on.

Pages bigger than the scanner arrive as several overlapping scans: stitch them (`scripts/photo_tools.py stitch OUT scan1 scan2 ... --base N`, where N points at a scan that is right way up - the page is built in that scan's orientation), keeping the sharpest scan wherever pieces overlap, then level the whole page. Say plainly if any strip of the page was never captured.

If two scans show the same print, keep the sharper, higher-resolution one and note the swap in the `.txt`. Don't add a duplicate slide.

## Enhancement - gentle beats dramatic

- **Black-and-white and sepia prints**: stretch the levels, add a little local contrast on lightness only, and lightly sharpen. Keep the sepia tone - turning it grey looks wrong to families. `photo_tools.py enhance --mode gentle`.
- **Faded colour prints** (red, magenta or yellow casts): per-channel levels plus a mild grey-world balance. `photo_tools.py enhance --mode color`. Crop off the white print border *before* correcting, or the border turns cyan.
- **Try 2-4 strengths side by side** on anything badly faded and pick the most natural. Over-correction (cyan skies, grey skin, pink sepia) is the common failure.
- **Leave good photos alone.** Well-exposed colour snapshots, faces in close-up, and halftone newspaper reproductions usually look worse after enhancing (harsh skin, visible dot pattern). Use the original and say why.
- The `Enhanced/` folder is curated by the family. If they delete an enhanced copy, that's a decision - use the original from then on and never regenerate it.

## Names, people and dates

- **Never identify people from their faces.** Name people only when the family tells you, a caption says so, or a newspaper names them. If asked "who is this?", say you can't tell from a face and describe what you can see (clothes, setting, what's written on the page) so they can decide.
- Use one spelling per person everywhere, the way the family says it ("Bobbie" not "Barbara"; "Kathleen" not "Kathy") - ask once which they prefer and remember it. Printed sources keep their original wording.
- Order people "L to R" only when the family gives the order.
- **Date from the strongest evidence**: handwritten caption → newspaper → phone camera data (EXIF) → lab date stamp (the month the film was *developed*, so the photo is that month or earlier) → family recollection → your estimate from ages and setting. Mark estimates "c." and add "(estimated)" on the slide.
- Check estimates against the person's birth date - "1940s" for someone who is visibly in her forties is a classic mistake.
- Many memorials are informal. If the family says approximate dates are fine, take their date and move on; stop asking for exact years.

## Chapters

Use the life story, not the album order - a single album page often mixes decades. If a written biography or timeline exists, make the chapters match its sections so the photos and the text line up. Typical chapters: early life, marriage and young family, the working/farming/career years, the middle years, a signature achievement, later years and grandchildren.

## Collages and pairs

- **Collages** for groups that would otherwise be repetitive slides: a trip, a house, "the cows", a set of postcards. Build with `photo_tools.py collage`, which tries every row split and keeps the one that fills the slide best. The pieces stay in `Separated/` and are listed in the README, but only the collage gets a slide.
- **Pairs** (two images side by side on one slide) for: the front and signed back of a photo, a photo and its keepsake (napkin, card), or a tall newspaper clipping split into its photo and its article.
- Let the family re-arrange: "remove the top left", "put 140 lower left" should be one quick rebuild.

## Documents that aren't photos

Memoir essays, letters, obituaries and newspaper articles are gold for captions but usually don't belong on slides. Transcribe them word for word into a Markdown file (mark illegible words in [brackets], keep original spelling), cite them from the timeline, and quote them in captions where they add warmth. Note, gently and separately, any historical details the memory got wrong - never "correct" the quote itself.

## The slideshow

Build with `scripts/build_deck.js` from a manifest (format in `references/deck-manifest.md`). It uses pptxgenjs and produces:

- a dark title slide with the chosen cover portrait,
- a dark divider per chapter (title, 1-2 sentence summary, a key photo),
- one white slide per photo: photo large and centred, then one line with **date + title**, then the caption, then a small grey source line; speaker notes repeat everything, including research sources,
- pair and triple layouts, and a closing slide.

After every build: run the pptx skill's `validate.py`, confirm the slide count, render the changed slides to images and look at them. Save to the same file name each time so the family's link keeps working. Opening in Google Slides: right-click in Drive → Open with → Google Slides (fine under 100 MB).

Handy numbers to offer: slides × seconds per slide ÷ 60 = running time (125 slides at 5 s ≈ 10½ min).

## Keeping the family oriented

- After each change, say in a sentence or two what changed and which slide it's on. Don't recite the whole deck.
- Photos left out of the slideshow "at the family's request" stay in the folders and are listed in the README - removal from the slides is not deletion.
- Keep a short "Still to check" list in the README (unnamed people, estimated dates, pages not fully scanned) instead of asking every question in chat.

## Tools

- `scripts/photo_tools.py` - `measure-tilt`, `straighten`, `enhance` (gentle / color), `collage`, `stitch`, `contact-sheet`. Run with `--help` on any subcommand. Needs Pillow, numpy, scipy, scikit-image, opencv-python-headless (make a venv in the scratch area if they're missing).
- `scripts/build_deck.js` - slideshow builder (needs `pptxgenjs`; `npm install pptxgenjs` in a scratch folder if `require` fails).
- `references/deck-manifest.md` - the manifest format the deck builder reads.
