# Deck manifest format

`scripts/build_deck.js manifest.json out.pptx` reads one JSON file. Generate it from the master photo list every time; don't edit it by hand.

Image entries need pixel `w` and `h` (for layout) and a path to a JPEG. Downscale images to ~1600 px on the long side first, or the deck gets huge (100+ photos at full scan size can pass Google Slides' 100 MB import limit).

```json
{
  "title": "Barbara \"Bobbie\"\nBlackledge Restle",
  "years": "1926 – 2026",
  "subtitle": "A life in photographs, from Paris and Egypt to the Indiana wetland she gave back to nature.",
  "cover": {"img": "img/cover.jpg", "w": 1200, "h": 1670, "title": "Studio portrait, c. 1962"},
  "colors": {"dark": "1F3A2E", "gold": "C9A461"},
  "sections": [
    {
      "name": "Early life (to the 1940s)",
      "summary": "Born in Paris in 1926 ... came to Teaneck, New Jersey around 1938.",
      "key": {"img": "img/35.jpg", "w": 1100, "h": 1500},
      "photos": [
        {
          "img": "img/37.jpg", "w": 1600, "h": 1200,
          "date": "1931", "estimated": false,
          "title": "Audrey and Claire (twins), Bobbie and Dick - Baden bei Wien",
          "caption": "Handwritten on the page: \"Baden/Wien 1931.\"",
          "source": "Album Scan 18 · photo #37",
          "notes": "Optional extra text for the speaker notes only, e.g. research sources."
        },
        {
          "type": "pair",
          "date": "Summer 1943", "title": "Senior Youth Conference",
          "caption": "...",
          "source": "Album Scans 59-60 · photos #137-#138",
          "imgs": [
            {"img": "img/137.jpg", "w": 1600, "h": 1380, "label": "Front"},
            {"img": "img/138.jpg", "w": 1600, "h": 1250, "label": "Signed back"}
          ]
        }
      ]
    }
  ],
  "closing": {
    "title": "Her gift keeps growing",
    "stats": [["1992", "The Restle Unit is dedicated ..."], ["824", "Acres now protected ..."], ["100", "Years of a life ..."]],
    "footnote": "Photos from the family albums, scanned 2026."
  }
}
```

Field notes:
- `estimated: true` adds "(estimated)" after the date - use it for any date you worked out yourself.
- `imgs` with 2 or 3 entries makes a side-by-side slide (front/back, photo + keepsake, a split clipping, three newspaper front pages). A collage is just a single image made with `photo_tools.py collage`.
- `key` is the photo shown on the chapter divider; it defaults to the chapter's first photo.
- `source` is the small grey line at the bottom of the slide; keep it short.
- `notes` is only in the speaker notes - the right place for citations and research links.
