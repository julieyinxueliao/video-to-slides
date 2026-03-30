---
name: youtube-to-slides
description: >
  Convert YouTube videos into beautiful, structured HTML presentation slides that surface the core ideas and key insights. Use this skill whenever a user provides a YouTube link and wants to understand, summarize, study, or share the video's content — even if they don't explicitly say "slides". Triggers on: any YouTube URL + intent to learn/summarize/present, "把这个YouTube视频做成slides", "帮我总结这个视频", "YouTube视频关键点提取", "make slides from this video", "summarize this YouTube", "create a presentation from this video", "视频转PPT", "YouTube to presentation", or any request to extract, digest, or visualize a YouTube video's content.
---

# YouTube to Slides

Convert YouTube long-form videos into beautiful, self-contained HTML presentation slides — modern editorial design, diverse layouts, content that makes the viewer say "I get it now."

---

## Workflow Overview

```
1. Extract transcript  →  2. Analyze content  →  3. Match layout to content  →  4. Generate HTML
```

The key insight driving this workflow: **different types of content deserve different visual treatments.** A bold claim deserves a quote slide. A framework deserves a diagram. A comparison deserves two columns. Don't default to bullets when a better shape exists.

---

## Step 1: Extract the Transcript

### Method A: Python script — `scripts/fetch_transcript.py` ← use this first

No API key required. Auto-installs `youtube-transcript-api` on first run. Works wherever Python has internet access (Claude Code, local terminal).

```bash
python scripts/fetch_transcript.py "YOUTUBE_URL_OR_VIDEO_ID"
```

Output is JSON:
```json
{
  "video_id": "abc123",
  "title": "Video Title",
  "channel": "Channel Name",
  "duration": "18m 4s",
  "language": "en",
  "transcript_text": "full plain text of the whole video...",
  "transcript_timestamped": "[0:00] Hello\n[0:04] Today we'll cover..."
}
```

Use `transcript_timestamped` for content analysis — timestamps help you identify section boundaries and chapter breaks. Use `title`, `channel`, `duration` for the cover slide.

### Method B: Browser fallback (when Python script can't reach YouTube)

If Method A fails (proxy/firewall), use Claude in Chrome to navigate to the page:

1. Navigate to the YouTube URL
2. Click "..." → **"Show transcript"** to open the transcript panel
3. Extract with JavaScript:

```javascript
const segments = document.querySelectorAll('ytd-transcript-segment-renderer');
const transcript = Array.from(segments).map(seg => {
  const time = seg.querySelector('.segment-timestamp')?.textContent?.trim() || '';
  const text = seg.querySelector('.segment-text')?.textContent?.trim() || '';
  return `[${time}] ${text}`;
}).filter(l => l.includes(']')).join('\n');
console.log(transcript);
```

Grab metadata via browser too:
```javascript
const title = document.querySelector('h1.ytd-watch-metadata yt-formatted-string')?.textContent?.trim()
  || document.title.replace(' - YouTube', '');
const channel = document.querySelector('ytd-channel-name yt-formatted-string a')?.textContent?.trim() || '';
console.log(JSON.stringify({ title, channel }));
```

### If no transcript exists

Use video title, description, and any chapter markers. Tell the user upfront.

---

## Step 1b: Find Related Videos

Search for 3–4 related videos to populate the final slide. Use whichever method is available:

**If you have web search access:** search for `"[VIDEO_TOPIC] youtube"` and find real YouTube URLs from the results. Extract the video ID (`v=` param), title, and channel.

**If you have browser access:** navigate to `https://www.youtube.com/results?search_query=[KEYWORDS]` and run:
```javascript
const results = document.querySelectorAll('ytd-video-renderer');
const videos = Array.from(results).slice(0, 6).map(el => {
  const titleEl = el.querySelector('#video-title');
  const channelEl = el.querySelector('ytd-channel-name a');
  const href = titleEl?.href || '';
  const id = new URLSearchParams(new URL(href || 'https://x.com?v=x').search).get('v');
  return { id, title: titleEl?.textContent?.trim(), channel: channelEl?.textContent?.trim() };
}).filter(v => v.id);
console.log(JSON.stringify(videos, null, 2));
```

Pick videos that genuinely go deeper on the topic. Keep the 3–4 video IDs, titles, and channels for the `layout-related` slide.

---

## Step 2: Analyze and Structure the Content

Read the transcript carefully — this is where insight happens. You're looking for the **narrative architecture**: what problem does the speaker open with, how do they build their argument, what's the twist or revelation, and what do they want you to do with it?

**Extraction checklist:**

| Element | What to look for |
|---------|-----------------|
| **Thesis** | What is the speaker ultimately arguing or teaching? |
| **Arc** | How does the talk build — problem → insight → solution? story → data → conclusion? |
| **Major sections** | Where do topics shift? Look for "first/second/finally", chapter timestamps, tone changes |
| **Key claims** | The 3–5 most important assertions |
| **Evidence & examples** | Specific stories, data points, case studies |
| **Frameworks/models** | Conceptual systems the speaker introduces (Golden Circle, 80/20, etc.) |
| **Memorable phrases** | Quotable, vivid, or surprising language worth preserving verbatim |
| **Conclusion** | The call to action or lasting impression |

**Target slide count** (cover + TOC + content + takeaways + related):
- < 15 min → 9–11 total (7–9 content slides)
- 15–30 min → 11–15 total
- 30–60 min → 15–19 total
- > 60 min → 19–24 total (theme clusters, not chronology)

**Before generating any HTML**, sketch the full slide plan AND produce the JavaScript `SLIDE_MAP` array:

```
Slide 0: cover           — (no timestamp — skip from SLIDE_MAP)
Slide 1: toc             — (no timestamp — skip from SLIDE_MAP)
Slide 2: [section title] — layout-X — starts at [M:SS] → [SECONDS]s
Slide 3: [section title] — layout-X — starts at [M:SS] → [SECONDS]s
...
Slide N-1: takeaways     — (no timestamp — skip from SLIDE_MAP)
Slide N:   related       — (no timestamp — skip from SLIDE_MAP)
```

Then translate that into the SLIDE_MAP JavaScript array (only content slides — not cover/toc/takeaways/related):
```javascript
const SLIDE_MAP = [
  { slideIndex: 2, startSec: [SECONDS], title: "[SECTION_2_TITLE]" },
  { slideIndex: 3, startSec: [SECONDS], title: "[SECTION_3_TITLE]" },
  // …one entry per content slide…
];
```

This single array drives: (1) the TOC links, (2) the video→slides auto-advance sync, and (3) the slides→video reverse seek.

---

## Step 3: Choose Layouts — Match the Content Shape

This is the creative heart of the skill. For each piece of content, ask: **"What visual form best communicates this?"**

### Layout library (10 types)

**1. `layout-cover`** — Use for: opening slide only
Visual: Large editorial headline, channel/duration metadata, one-line thesis. No thumbnail — the video is already playing on the left panel.

**2. `layout-toc`** — Use for: ALWAYS the second slide (right after cover)
Visual: Numbered list of every content section in the deck. Each row is a clickable link that jumps directly to that slide. Gives viewers the full map before diving in.

**3. `layout-list`** — Use for: arguments, steps, features, general key points
Visual: Section label → H2 → 3–5 animated bullets. Each bullet is one complete thought, not a fragment.

**4. `layout-quote`** — Use for: verbatim speaker quotes, key insights, surprising statements
Visual: Full-slide treatment. Large italic quote text, colored left border, speaker attribution.

**5. `layout-two-col`** — Use for: comparisons, before/after, problem/solution, contrasting approaches
Visual: Left label + content | Right label + content, separated by a thin divider line.

**6. `layout-stat`** — Use for: single impactful numbers, research statistics, percentages
Visual: Huge number centered, short descriptor below, context note at bottom.

**7. `layout-grid`** — Use for: 3–4 distinct concepts, named principles, enumerated framework elements
Visual: 2×2 or 1×3 grid, each cell has an emoji icon, a short label, and 1-sentence description.

**8. `layout-table`** — Use for: structured comparisons with multiple attributes, feature matrices
Visual: Clean borderless table with shaded header row.

**9. `layout-framework`** — Use for: conceptual models, hierarchies, processes, diagrams (e.g. Golden Circle, funnel, timeline)
Visual: CSS-based diagram using nested boxes, circles, or flow arrows. No images needed.

**10. `layout-chart`** — Use for: proportions/distributions (pie), quantities compared across categories (bar), change over time (bar)
Visual: CSS-only charts (conic-gradient pie or flex bar) with a legend. No external JS library needed.
- **Pie/donut variant**: use when the speaker gives % breakdowns, audience segments, time allocation, or anything that sums to a whole.
- **Bar variant**: use when comparing magnitudes across discrete categories — e.g. revenue by region, adoption rates, test scores by group.

### Decision heuristic

```
Is this the very first slide?                           → layout-cover
Is this the very second slide?                          → layout-toc
Does the content involve a direct quote?                → layout-quote
Does it show proportions / percentage breakdown?        → layout-chart (pie)
Does it compare quantities across categories?           → layout-chart (bar)
Does it compare two things side by side (no numbers)?   → layout-two-col
Is there a single striking number?                      → layout-stat
Does it describe a named model/framework?               → layout-framework
Are there exactly 3–4 parallel concepts with labels?    → layout-grid
Are there 3+ things with multiple attributes?           → layout-table
Otherwise                                               → layout-list
```

Apply this to every section of the transcript. Aim for **no more than 2 consecutive `layout-list` slides** — variety signals effort and aids comprehension.

---

## Step 4: Generate the HTML

Build a single self-contained `.html` file. The design system below is mandatory — it creates the Granola-inspired "calm editorial energy" aesthetic.

### Design system

**Typography** (load via Google Fonts CDN):
- `DM Serif Display` — headings and display text (editorial slab serif with character)
- `Inter` — body text, labels, metadata (clean, modern, readable at all sizes)

**Color palette** (dark mode by default):
```
--bg:       #111110   /* warm near-black, not pure #000 */
--surface:  #1A1A18   /* slightly elevated surface */
--border:   rgba(255,255,255,0.08)
--text:     #F0EBE0   /* warm off-white, not harsh */
--muted:    rgba(240,235,224,0.45)
--accent:   #5C8A6B   /* sage green — Granola's signature tone */
--accent2:  #8BAF78   /* lighter sage for hover/highlight */
--highlight: rgba(92,138,107,0.15)  /* for pill/badge backgrounds */
```

**Type scale** (base: `18px` — sized to fit comfortably within the half-screen slide panel):
- Cover headline: `2.6em` (~47px), `DM Serif Display`, italic
- H2 (slide title): `1.65em` (~30px), `DM Serif Display`, italic
- Body / bullet: `0.84em` (~15px), `Inter`, line-height `1.65`
- Label / overline: `0.42em` (~7.5px), `Inter`, uppercase, `letter-spacing: 0.18em`
- Small context / attribution: `0.52em` (~9.4px) — never go below this
- Card body text: `0.65em` (~11.7px)

**Spacing & feel:**
- Generous padding: `60px` horizontal on slide content
- Section divider: `2px solid var(--accent)` at `40px` width (decorative accent, not full-width line)
- Rounded corners: `10px` for cards, `6px` for badges
- Transitions: `opacity 0.35s ease` for fragments

---

### Complete HTML template

Use this as your starting point. Replace all `[PLACEHOLDERS]`.

**Layout**: The page is split 50/50 — video player on the left, Reveal.js slides on the right. As the video plays, slides auto-advance. Clicking a slide seeks the video to the corresponding moment. Reveal.js must use `embedded: true` so it runs inside a div rather than fullscreen.

```html
<!DOCTYPE html>
<html lang="[LANG_CODE]">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[VIDEO_TITLE] — Slides</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600&display=swap">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.6.1/reveal.min.css">
  <style>
    /* ── Page reset ── */
    *, *::before, *::after { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #111110; }

    /* ── Split-screen app shell ── */
    #app {
      display: flex;
      align-items: stretch;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
    }

    /* ── Left: video panel ── */
    #video-panel {
      width: 50%;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
      background: #0D0D0C;
      padding: 10px;
    }
    #player-wrap {
      position: relative;
      width: 100%;
      padding-top: 56.25%; /* 16:9 */
      background: #000;
    }
    #yt-player {
      position: absolute;
      inset: 0;
      width: 100% !important;
      height: 100% !important;
    }
    /* Chapter indicator bar */
    #chapter-bar {
      flex-shrink: 0;
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 20px;
      border-top: 1px solid rgba(255,255,255,0.06);
      min-height: 44px;
    }
    #sync-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #5C8A6B;
      flex-shrink: 0;
      animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.35; }
    }
    #chapter-label {
      font-family: 'Inter', sans-serif;
      font-size: 12px;
      color: rgba(240,235,224,0.55);
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    #chapter-time {
      font-family: 'Inter', sans-serif;
      font-size: 11px;
      color: rgba(240,235,224,0.3);
      flex-shrink: 0;
      letter-spacing: 0.05em;
    }

    /* ── Divider ── */
    #panel-divider {
      width: 1px;
      background: rgba(255,255,255,0.07);
      flex-shrink: 0;
    }

    /* ── Right: slides panel ── */
    #slides-panel {
      flex: 1;
      overflow: hidden;
      position: relative;
    }
    /* Reveal viewport must fill the slides panel exactly */
    #slides-panel .reveal-viewport,
    #slides-panel .reveal {
      width: 100% !important;
      height: 100% !important;
    }

    /* ── Design system ── */
    :root {
      --bg: #111110;
      --surface: #1A1A18;
      --border: rgba(255,255,255,0.08);
      --text: #F0EBE0;
      --muted: rgba(240,235,224,0.45);
      --accent: #5C8A6B;
      --accent2: #8BAF78;
      --highlight: rgba(92,138,107,0.15);
    }

    /* ── Reveal overrides ── */
    .reveal-viewport { background: var(--bg); }
    .reveal {
      font-family: 'Inter', sans-serif;
      font-size: 18px; /* base: sized to fit within the half-screen slide panel */
      color: var(--text);
    }
    .reveal .slides section {
      text-align: left;
      padding: 0 60px;
      box-sizing: border-box;
    }
    .reveal h1, .reveal h2 {
      font-family: 'DM Serif Display', serif;
      font-style: italic;
      color: var(--text);
      text-transform: none;
      letter-spacing: -0.01em;
      line-height: 1.15;
    }
    .reveal h1 { font-size: 2.8em; }
    .reveal h2 { font-size: 1.65em; margin-bottom: 0.6em; }
    .reveal ul { list-style: none; padding: 0; }
    .reveal ul li {
      font-size: 0.84em;
      line-height: 1.65;
      padding: 0.25em 0 0.25em 1.2em;
      position: relative;
      color: var(--text);
    }
    .reveal ul li::before {
      content: '–';
      position: absolute;
      left: 0;
      color: var(--accent);
      font-weight: 600;
    }
    .reveal a { color: var(--accent2); }
    .reveal .progress span { background: var(--accent); }
    .reveal .controls { color: var(--accent); }
    .reveal .fragment { transition: opacity 0.35s ease, transform 0.35s ease; }
    .reveal .fragment.visible { opacity: 1; }

    /* ── Overline label ── */
    .label {
      display: block;
      font-family: 'Inter', sans-serif;
      font-size: 0.42em; /* ~11.8px at 28px base — minimum readable */
      text-transform: uppercase;
      letter-spacing: 0.18em;
      color: var(--muted);
      margin-bottom: 0.6em;
      font-weight: 500;
    }

    /* ── Accent bar (decorative) ── */
    .accent-bar {
      display: block;
      width: 36px;
      height: 2px;
      background: var(--accent);
      margin-bottom: 1em;
    }

    /* ── layout-toc (table of contents — always slide 2) ── */
    .layout-toc {
      display: flex !important;
      flex-direction: column;
      justify-content: center;
      min-height: 100% !important;
    }
    .layout-toc .toc-list {
      list-style: none;
      padding: 0;
      margin: 0.5em 0 0;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 0.15em 2em;
    }
    .layout-toc .toc-list li {
      padding: 0;
    }
    .layout-toc .toc-list li::before { display: none; }
    .layout-toc .toc-item {
      display: flex;
      align-items: baseline;
      gap: 0.6em;
      padding: 0.4em 0.5em;
      border-radius: 6px;
      text-decoration: none;
      transition: background 0.15s;
      cursor: pointer;
    }
    .layout-toc .toc-item:hover { background: var(--highlight); }
    .layout-toc .toc-num {
      font-family: 'DM Serif Display', serif;
      font-style: italic;
      font-size: 0.7em;
      color: var(--accent);
      min-width: 1.4em;
      flex-shrink: 0;
    }
    .layout-toc .toc-title {
      font-family: 'Inter', sans-serif;
      font-size: 0.72em; /* ~20.2px */
      color: var(--text);
      line-height: 1.4;
    }
    .layout-toc .toc-time {
      font-size: 0.5em;
      color: var(--muted);
      margin-left: auto;
      flex-shrink: 0;
      padding-left: 0.5em;
    }

    /* ── layout-cover ── */
    .layout-cover {
      display: flex !important;
      flex-direction: column;
      justify-content: center;
      text-align: left !important;
      min-height: 100% !important;
    }
    .layout-cover h1 {
      font-size: 2.6em;
      line-height: 1.15;
      margin-bottom: 0.5em;
    }
    .layout-cover .meta {
      font-size: 0.5em;
      color: var(--muted);
      font-family: 'Inter', sans-serif;
      margin-bottom: 1.5em;
      display: flex;
      gap: 1.2em;
      align-items: center;
    }
    .layout-cover .meta span { display: flex; align-items: center; gap: 0.3em; }
    .layout-cover .thesis {
      font-size: 0.72em;
      font-family: 'Inter', sans-serif;
      color: var(--muted);
      border-left: 2px solid var(--accent);
      padding-left: 0.9em;
      line-height: 1.6;
      max-width: 85%;
    }

    /* ── layout-quote ── */
    .layout-quote {
      display: flex !important;
      flex-direction: column;
      justify-content: center;
      min-height: 100% !important;
    }
    .layout-quote blockquote {
      font-family: 'DM Serif Display', serif;
      font-style: italic;
      font-size: 1.3em;
      line-height: 1.5;
      color: var(--text);
      margin: 0;
      padding: 0;
      border: none;
      box-shadow: none;
      background: none;
    }
    .layout-quote .attribution {
      margin-top: 1.2em;
      font-size: 0.52em; /* ~14.6px — comfortably readable */
      color: var(--muted);
      font-family: 'Inter', sans-serif;
      letter-spacing: 0.05em;
    }

    /* ── layout-two-col ── */
    .layout-two-col .cols {
      display: grid;
      grid-template-columns: 1fr 1px 1fr;
      gap: 2em;
      align-items: start;
      margin-top: 0.5em;
    }
    .layout-two-col .divider { background: var(--border); }
    .layout-two-col .col-label {
      font-size: 0.46em; /* ~12.9px */
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: var(--accent2);
      font-weight: 600;
      margin-bottom: 0.5em;
    }
    .layout-two-col ul li { font-size: 0.8em; }

    /* ── layout-stat ── */
    .layout-stat {
      display: flex !important;
      flex-direction: column;
      justify-content: center;
      min-height: 100% !important;
    }
    .layout-stat .stat-number {
      font-family: 'DM Serif Display', serif;
      font-size: 4.5em;
      line-height: 1;
      color: var(--accent2);
      margin: 0.15em 0 0.1em;
    }
    .layout-stat .stat-label {
      font-size: 0.9em;
      color: var(--text);
      margin-bottom: 0.8em;
    }
    .layout-stat .stat-context {
      font-size: 0.55em; /* ~15.4px */
      color: var(--muted);
      max-width: 60%;
      line-height: 1.6;
    }

    /* ── layout-grid ── */
    .layout-grid .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1em;
      margin-top: 0.8em;
    }
    .layout-grid .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1em 1.1em;
    }
    .layout-grid .card-icon { font-size: 1.4em; margin-bottom: 0.3em; }
    .layout-grid .card-title {
      font-family: 'DM Serif Display', serif;
      font-style: italic;
      font-size: 0.85em;
      margin-bottom: 0.3em;
      color: var(--text);
    }
    .layout-grid .card-body {
      font-size: 0.65em; /* ~18.2px */
      color: var(--muted);
      line-height: 1.5;
    }

    /* ── layout-table ── */
    .layout-table table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.68em;
      margin-top: 0.5em;
    }
    .layout-table th {
      background: var(--surface);
      color: var(--accent2);
      font-family: 'Inter', sans-serif;
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.75em;
      letter-spacing: 0.1em;
      padding: 0.6em 0.8em;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    .layout-table td {
      padding: 0.6em 0.8em;
      border-bottom: 1px solid var(--border);
      color: var(--text);
      line-height: 1.5;
    }
    .layout-table tr:last-child td { border-bottom: none; }
    .layout-table tr:hover td { background: var(--highlight); }

    /* ── layout-framework ── */
    /* CSS-only diagrams — see framework patterns below */
    .fw-stack {
      display: flex;
      flex-direction: column-reverse;
      gap: 0;
      max-width: 480px;
      margin: 0.8em auto;
    }
    .fw-stack .fw-layer {
      padding: 0.6em 1em;
      text-align: center;
      font-size: 0.72em; /* ~20.2px */
      font-weight: 500;
      border-radius: 4px;
      margin-bottom: 2px;
      color: var(--bg);
    }
    .fw-stack .fw-layer:nth-child(1) { background: var(--accent2); width: 100%; }
    .fw-stack .fw-layer:nth-child(2) { background: var(--accent); width: 80%; align-self: center; }
    .fw-stack .fw-layer:nth-child(3) { background: #3D6050; width: 55%; align-self: center; }

    .fw-circles {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: -1em;
      margin: 1em 0;
      position: relative;
      height: 200px;
    }
    .fw-circle {
      border-radius: 50%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: absolute;
      font-size: 0.62em; /* ~17.4px */
      text-align: center;
      font-weight: 500;
    }

    /* ── layout-related (related videos + share — always last) ── */
    .layout-related .rel-list { margin-top: 0.7em; }
    .layout-related .rel-row {
      display: flex;
      align-items: center;
      gap: 0.8em;
      padding: 0.6em 0.8em;
      border-radius: 8px;
      text-decoration: none;
      transition: background 0.18s;
      margin-bottom: 0.3em;
      border: 1px solid transparent;
    }
    .layout-related .rel-row:hover {
      background: var(--surface);
      border-color: var(--border);
    }
    .layout-related .rel-icon {
      color: var(--accent);
      font-size: 0.8em;
      flex-shrink: 0;
      margin-top: 0.1em;
    }
    .layout-related .rel-body { flex: 1; min-width: 0; }
    .layout-related .rel-title {
      font-family: 'Inter', sans-serif;
      font-size: 0.68em;
      font-weight: 500;
      color: var(--text);
      line-height: 1.4;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .layout-related .rel-channel {
      font-size: 0.52em;
      color: var(--muted);
      margin-top: 0.15em;
    }
    .layout-related .rel-arrow {
      color: var(--muted);
      font-size: 0.65em;
      flex-shrink: 0;
    }
    /* Share buttons */
    .share-row {
      display: flex;
      gap: 0.7em;
      margin-top: 1.4em;
      align-items: center;
    }
    .share-label {
      font-size: 0.48em;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-weight: 500;
      flex-shrink: 0;
    }
    .share-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.4em;
      padding: 0.35em 0.85em;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      font-family: 'Inter', sans-serif;
      font-size: 0.52em;
      font-weight: 500;
      text-decoration: none;
      cursor: pointer;
      transition: border-color 0.18s, background 0.18s;
    }
    .share-btn:hover { border-color: var(--accent); background: var(--highlight); }

    /* ── layout-takeaways ── */
    .takeaway-list { margin-top: 0.5em; }
    .takeaway-item {
      display: flex;
      align-items: flex-start;
      gap: 0.7em;
      background: var(--highlight);
      border: 1px solid rgba(92,138,107,0.25);
      border-radius: 8px;
      padding: 0.55em 0.9em;
      margin-bottom: 0.5em;
      font-size: 0.75em;
      line-height: 1.5;
    }
    .takeaway-item .ti-icon {
      color: var(--accent2);
      font-size: 1em;
      margin-top: 0.05em;
      flex-shrink: 0;
    }

    /* ── layout-chart ── */
    /* PIE / DONUT chart (CSS conic-gradient) */
    .chart-area {
      display: flex;
      align-items: center;
      gap: 2.5em;
      margin-top: 0.8em;
    }
    .pie-wrap {
      flex-shrink: 0;
      position: relative;
    }
    .pie {
      width: 160px;
      height: 160px;
      border-radius: 50%;
      /* Fill via inline style: background: conic-gradient(...) */
    }
    .pie-hole {
      position: absolute;
      inset: 30px;
      background: var(--bg);
      border-radius: 50%;
    }
    /* BAR chart (horizontal flex bars) */
    .bar-chart { width: 100%; margin-top: 0.8em; }
    .bar-row {
      display: flex;
      align-items: center;
      gap: 0.7em;
      margin-bottom: 0.55em;
    }
    .bar-label {
      font-size: 0.6em;
      color: var(--text);
      min-width: 130px;
      flex-shrink: 0;
      line-height: 1.3;
    }
    .bar-track {
      flex: 1;
      height: 22px;
      background: var(--surface);
      border-radius: 4px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      background: var(--accent);
      border-radius: 4px;
      transition: width 0.6s ease;
      /* Set width via inline style, e.g. style="width:72%" */
    }
    .bar-fill.bar-alt { background: var(--accent2); }
    .bar-val {
      font-size: 0.55em;
      color: var(--muted);
      min-width: 2.8em;
      text-align: right;
      flex-shrink: 0;
    }
    /* Shared legend */
    .chart-legend {
      flex: 1;
      min-width: 0;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 0.5em;
      margin-bottom: 0.5em;
      font-size: 0.6em;
      line-height: 1.4;
    }
    .legend-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .legend-name { color: var(--text); font-weight: 500; }
    .legend-pct  { color: var(--muted); margin-left: 0.3em; }
  </style>
</head>
<body>

<!-- ═══════════════════════════════════════════════════
     PAGE LAYOUT — left: video panel | right: slides panel
     The two panels share the full viewport height.
════════════════════════════════════════════════════════ -->
<div id="app">

  <!-- LEFT: Video panel -->
  <div id="video-panel">
    <div id="player-wrap">
      <div id="yt-player"></div>  <!-- YouTube IFrame mounts here -->
    </div>
    <!-- Chapter indicator bar — updates as video plays -->
    <div id="chapter-bar">
      <div id="sync-dot"></div>
      <span id="chapter-label">Loading…</span>
      <span id="chapter-time"></span>
    </div>
  </div>

  <!-- Divider -->
  <div id="panel-divider"></div>

  <!-- RIGHT: Slides panel (Reveal.js embedded) -->
  <div id="slides-panel">
    <div class="reveal">
      <div class="slides">

    <!-- ══════════════════════════════════════
         layout-cover  (always first)
         No thumbnail — the video already plays on the left panel.
    ══════════════════════════════════════ -->
    <section class="layout-cover">
      <span class="label">Video Summary</span>
      <span class="accent-bar"></span>
      <h1 style="font-size:2em; margin-bottom:0.4em;">[VIDEO_TITLE]</h1>
      <div class="meta">
        <span>📺 [CHANNEL_NAME]</span>
        <span>⏱ [DURATION]</span>
      </div>
      <div class="thesis">[ONE_SENTENCE_THESIS — the speaker's core argument in one sentence]</div>
    </section>

    <!-- ══════════════════════════════════════
         layout-toc  (ALWAYS slide 2 — table of contents)

         INSTRUCTIONS FOR GENERATING THIS SLIDE:
         1. Plan ALL content slides first (their titles and start timestamps)
         2. Assign 0-based indices: cover=0, toc=1, first_content=2, second=3, …
         3. Each toc-item href="#/N" where N is the target slide's 0-based index
         4. toc-time shows the start timestamp from the transcript (e.g. "2:14")
         5. Use onclick="Reveal.slide(N)" as fallback for hash navigation
    ══════════════════════════════════════ -->
    <section class="layout-toc">
      <span class="label">Contents</span>
      <span class="accent-bar"></span>
      <h2 style="font-size:1.4em; margin-bottom:0.4em;">What We'll Cover</h2>
      <ul class="toc-list">
        <!-- Repeat one <li> per content section. href="#/N" uses 0-based slide index. -->
        <li>
          <a class="toc-item" href="#/2" onclick="event.preventDefault(); Reveal.slide(2);">
            <span class="toc-num">01</span>
            <span class="toc-title">[SECTION_1_TITLE]</span>
            <span class="toc-time">[TIMESTAMP, e.g. "1:02"]</span>
          </a>
        </li>
        <li>
          <a class="toc-item" href="#/3" onclick="event.preventDefault(); Reveal.slide(3);">
            <span class="toc-num">02</span>
            <span class="toc-title">[SECTION_2_TITLE]</span>
            <span class="toc-time">[TIMESTAMP]</span>
          </a>
        </li>
        <li>
          <a class="toc-item" href="#/4" onclick="event.preventDefault(); Reveal.slide(4);">
            <span class="toc-num">03</span>
            <span class="toc-title">[SECTION_3_TITLE]</span>
            <span class="toc-time">[TIMESTAMP]</span>
          </a>
        </li>
        <!-- Add more rows as needed, incrementing href index and toc-num -->
      </ul>
    </section>

    <!-- ══════════════════════════════════════
         layout-list  (arguments, steps, key points)
    ══════════════════════════════════════ -->
    <section>
      <span class="label">[SECTION_LABEL, e.g. "Part 1 · The Problem"]</span>
      <h2>[SLIDE_TITLE]</h2>
      <ul>
        <li class="fragment">[KEY_POINT_1 — a complete thought, 8–12 words]</li>
        <li class="fragment">[KEY_POINT_2]</li>
        <li class="fragment">[KEY_POINT_3]</li>
        <!-- max 5 bullets; if more, split into two slides -->
      </ul>
      <!-- Optional: supporting note -->
      <!-- <p style="font-size:0.52em; color:var(--muted); margin-top:1em;">[DETAIL]</p> -->
    </section>

    <!-- ══════════════════════════════════════
         layout-quote  (verbatim quotes, key insights)
    ══════════════════════════════════════ -->
    <section class="layout-quote">
      <span class="label">Key Insight</span>
      <span class="accent-bar"></span>
      <blockquote>"[VERBATIM_QUOTE]"</blockquote>
      <div class="attribution">— [SPEAKER], [CONTEXT, e.g. "~14:30"]</div>
    </section>

    <!-- ══════════════════════════════════════
         layout-two-col  (comparisons, before/after)
    ══════════════════════════════════════ -->
    <section class="layout-two-col">
      <span class="label">[SECTION_LABEL]</span>
      <h2>[SLIDE_TITLE, e.g. "What vs. Why"]</h2>
      <div class="cols">
        <div class="col-left">
          <div class="col-label">[LEFT_LABEL, e.g. "Most Companies"]</div>
          <ul>
            <li>[POINT_A1]</li>
            <li>[POINT_A2]</li>
          </ul>
        </div>
        <div class="divider"></div>
        <div class="col-right">
          <div class="col-label">[RIGHT_LABEL, e.g. "Great Leaders"]</div>
          <ul>
            <li>[POINT_B1]</li>
            <li>[POINT_B2]</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════
         layout-stat  (single striking number)
    ══════════════════════════════════════ -->
    <section class="layout-stat">
      <span class="label">[SECTION_LABEL]</span>
      <div class="stat-number">[NUMBER, e.g. "98%"]</div>
      <div class="stat-label">[WHAT_IT_MEANS, e.g. "of children test as creative geniuses at age 5"]</div>
      <div class="stat-context">[SOURCE_OR_CONTEXT, e.g. "From George Land's 1968 NASA divergent thinking study, cited in the talk"]</div>
    </section>

    <!-- ══════════════════════════════════════
         layout-grid  (3–4 named concepts)
    ══════════════════════════════════════ -->
    <section class="layout-grid">
      <span class="label">[SECTION_LABEL]</span>
      <h2>[SLIDE_TITLE]</h2>
      <div class="grid">
        <div class="card fragment">
          <div class="card-icon">[EMOJI_1]</div>
          <div class="card-title">[CONCEPT_1]</div>
          <div class="card-body">[1-SENTENCE_DESCRIPTION]</div>
        </div>
        <div class="card fragment">
          <div class="card-icon">[EMOJI_2]</div>
          <div class="card-title">[CONCEPT_2]</div>
          <div class="card-body">[1-SENTENCE_DESCRIPTION]</div>
        </div>
        <div class="card fragment">
          <div class="card-icon">[EMOJI_3]</div>
          <div class="card-title">[CONCEPT_3]</div>
          <div class="card-body">[1-SENTENCE_DESCRIPTION]</div>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════
         layout-table  (structured comparison)
    ══════════════════════════════════════ -->
    <section class="layout-table">
      <span class="label">[SECTION_LABEL]</span>
      <h2>[SLIDE_TITLE]</h2>
      <table>
        <thead>
          <tr>
            <th>[COL_1]</th>
            <th>[COL_2]</th>
            <th>[COL_3]</th>
          </tr>
        </thead>
        <tbody>
          <tr class="fragment">
            <td>[VALUE]</td><td>[VALUE]</td><td>[VALUE]</td>
          </tr>
          <tr class="fragment">
            <td>[VALUE]</td><td>[VALUE]</td><td>[VALUE]</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ══════════════════════════════════════
         layout-framework  (conceptual model)
         Example: nested circles (Golden Circle)
    ══════════════════════════════════════ -->
    <section>
      <span class="label">[SECTION_LABEL]</span>
      <h2>[MODEL_NAME]</h2>
      <!-- OPTION A: Pyramid / layered stack -->
      <div class="fw-stack">
        <div class="fw-layer">[OUTER_LAYER, e.g. "WHAT — Products & services"]</div>
        <div class="fw-layer">[MIDDLE_LAYER, e.g. "HOW — Differentiating process"]</div>
        <div class="fw-layer">[CORE_LAYER, e.g. "WHY — Purpose & belief"]</div>
      </div>
      <!-- OPTION B: Annotated list describing the model's levels -->
      <!-- Use whichever fits; remove unused option -->
      <p style="font-size:0.5em; color:var(--muted); text-align:center; margin-top:0.5em;">[BRIEF_EXPLANATION]</p>
    </section>

    <!-- ══════════════════════════════════════
         layout-chart  OPTION A: PIE / DONUT
         Use when content describes proportions or % breakdown of a whole.
         Colors: use var(--accent), var(--accent2), and similar green/earth tones.
         conic-gradient: each segment is "COLOR START_PCT% END_PCT%"
         e.g. 3 segments: 40%, 35%, 25%
           conic-gradient(#5C8A6B 0% 40%, #8BAF78 40% 75%, #3D6050 75% 100%)
    ══════════════════════════════════════ -->
    <section class="layout-chart">
      <span class="label">[SECTION_LABEL]</span>
      <h2>[SLIDE_TITLE, e.g. "How People Spend Their Time"]</h2>
      <div class="chart-area">
        <div class="pie-wrap">
          <!-- Compute cumulative percentages and plug into conic-gradient -->
          <div class="pie" style="background: conic-gradient(
            #5C8A6B 0% [PCT_1]%,
            #8BAF78 [PCT_1]% [PCT_1_PLUS_2]%,
            #3D6050 [PCT_1_PLUS_2]% [PCT_1_PLUS_2_PLUS_3]%,
            #2A4A38 [PCT_1_PLUS_2_PLUS_3]% 100%
          );"></div>
          <div class="pie-hole"></div>
        </div>
        <div class="chart-legend">
          <div class="legend-item fragment">
            <div class="legend-dot" style="background:#5C8A6B;"></div>
            <span class="legend-name">[CATEGORY_1]</span>
            <span class="legend-pct">[PCT_1]%</span>
          </div>
          <div class="legend-item fragment">
            <div class="legend-dot" style="background:#8BAF78;"></div>
            <span class="legend-name">[CATEGORY_2]</span>
            <span class="legend-pct">[PCT_2]%</span>
          </div>
          <div class="legend-item fragment">
            <div class="legend-dot" style="background:#3D6050;"></div>
            <span class="legend-name">[CATEGORY_3]</span>
            <span class="legend-pct">[PCT_3]%</span>
          </div>
          <!-- Add more legend items as needed -->
          <p style="font-size:0.52em; color:var(--muted); margin-top:0.9em; line-height:1.5;">[CONTEXT_NOTE — source or explanation]</p>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════
         layout-chart  OPTION B: HORIZONTAL BAR
         Use when comparing quantities across discrete categories.
         Set each .bar-fill width as inline style: style="width:72%"
         Use bar-alt class for alternating color if helpful.
    ══════════════════════════════════════ -->
    <section class="layout-chart">
      <span class="label">[SECTION_LABEL]</span>
      <h2>[SLIDE_TITLE, e.g. "Adoption by Region"]</h2>
      <div class="bar-chart">
        <div class="bar-row fragment">
          <div class="bar-label">[CATEGORY_1]</div>
          <div class="bar-track"><div class="bar-fill" style="width:[PCT_1]%;"></div></div>
          <div class="bar-val">[VALUE_1]</div>
        </div>
        <div class="bar-row fragment">
          <div class="bar-label">[CATEGORY_2]</div>
          <div class="bar-track"><div class="bar-fill bar-alt" style="width:[PCT_2]%;"></div></div>
          <div class="bar-val">[VALUE_2]</div>
        </div>
        <div class="bar-row fragment">
          <div class="bar-label">[CATEGORY_3]</div>
          <div class="bar-track"><div class="bar-fill" style="width:[PCT_3]%;"></div></div>
          <div class="bar-val">[VALUE_3]</div>
        </div>
        <!-- Add more rows as needed -->
      </div>
      <p style="font-size:0.52em; color:var(--muted); margin-top:0.6em;">[CONTEXT_NOTE]</p>
    </section>

    <!-- ══════════════════════════════════════
         layout-takeaways  (always second-to-last, before related)
         No ts-link needed on this slide.
    ══════════════════════════════════════ -->
    <section>
      <span class="label">Takeaways</span>
      <h2>[TAKEAWAYS_TITLE, e.g. "What To Carry Forward"]</h2>
      <div class="takeaway-list">
        <div class="takeaway-item fragment">
          <span class="ti-icon">→</span>
          <span>[TAKEAWAY_1 — actionable or memorable insight]</span>
        </div>
        <div class="takeaway-item fragment">
          <span class="ti-icon">→</span>
          <span>[TAKEAWAY_2]</span>
        </div>
        <div class="takeaway-item fragment">
          <span class="ti-icon">→</span>
          <span>[TAKEAWAY_3]</span>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════
         layout-related  (ALWAYS the very last slide)
         NO thumbnail images — just clean text rows with title + channel.
         Share buttons use the original YouTube URL of the video being summarised.
         The JS block at the bottom auto-fills share URLs from data-url attribute.
    ══════════════════════════════════════ -->
    <section class="layout-related" data-yt-url="[FULL_YOUTUBE_URL]" data-yt-title="[VIDEO_TITLE_URL_ENCODED]">
      <span class="label">Go Further</span>
      <h2 style="font-size:1.3em; margin-bottom:0.2em;">Related Videos</h2>

      <div class="rel-list">

        <a class="rel-row" href="https://www.youtube.com/watch?v=[REL_VIDEO_ID_1]" target="_blank">
          <span class="rel-icon">▶</span>
          <div class="rel-body">
            <div class="rel-title">[REL_TITLE_1]</div>
            <div class="rel-channel">[REL_CHANNEL_1]</div>
          </div>
          <span class="rel-arrow">↗</span>
        </a>

        <a class="rel-row" href="https://www.youtube.com/watch?v=[REL_VIDEO_ID_2]" target="_blank">
          <span class="rel-icon">▶</span>
          <div class="rel-body">
            <div class="rel-title">[REL_TITLE_2]</div>
            <div class="rel-channel">[REL_CHANNEL_2]</div>
          </div>
          <span class="rel-arrow">↗</span>
        </a>

        <a class="rel-row" href="https://www.youtube.com/watch?v=[REL_VIDEO_ID_3]" target="_blank">
          <span class="rel-icon">▶</span>
          <div class="rel-body">
            <div class="rel-title">[REL_TITLE_3]</div>
            <div class="rel-channel">[REL_CHANNEL_3]</div>
          </div>
          <span class="rel-arrow">↗</span>
        </a>

      </div>

      <!-- Share buttons — JS below fills in the correct URLs at runtime -->
      <div class="share-row">
        <span class="share-label">Share</span>
        <a class="share-btn" id="share-email" href="#" target="_blank">
          ✉ Email
        </a>
        <a class="share-btn" id="share-linkedin" href="#" target="_blank">
          in LinkedIn
        </a>
        <a class="share-btn" id="share-x" href="#" target="_blank">
          𝕏 X
        </a>
      </div>
    </section>

      </div><!-- /.slides -->
    </div><!-- /.reveal -->
  </div><!-- /#slides-panel -->

</div><!-- /#app -->

<!-- ═══════════════════════════════════════════════════════════
     SCRIPTS
     Load order: Reveal.js → YouTube IFrame API → init both
════════════════════════════════════════════════════════════ -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.6.1/reveal.min.js"></script>
<script>
  // ── 1. SLIDE TIMESTAMP MAP ──────────────────────────────────
  // Generated during slide planning in Step 2.
  // One entry per CONTENT slide (skip cover, toc, takeaways, related).
  // startSec: convert [M:SS] transcript timestamp → minutes*60+seconds
  const SLIDE_MAP = [
    { slideIndex: 2, startSec: [SECONDS_2], title: "[SECTION_2_TITLE]" },
    { slideIndex: 3, startSec: [SECONDS_3], title: "[SECTION_3_TITLE]" },
    // … one entry per content slide …
  ];

  // ── 2. DYNAMIC FONT SIZE — scales with the slides panel width ──
  function fitFontSize() {
    var panel = document.getElementById('slides-panel');
    var el = document.querySelector('#slides-panel .reveal');
    if (!el) return;
    var size = Math.max(11, Math.min(panel.offsetWidth / 42, 22));
    el.style.fontSize = size + 'px';
  }
  window.addEventListener('resize', fitFontSize);

  // ── 3. REVEAL.JS INIT (embedded mode — runs in a div, not fullscreen) ──
  Reveal.initialize({
    embedded: true,       // ← critical: confines Reveal to #slides-panel
    hash: false,          // we control navigation programmatically
    controls: true,
    progress: true,
    slideNumber: 'c/t',
    transition: 'fade',
    transitionSpeed: 'slow',
    backgroundTransition: 'fade',
    center: true,         // vertically center slide content
    margin: 0.04,
    width: '100%',
    height: '100%',
  }).then(function() { fitFontSize(); }); // run after Reveal sets its own font-size

  // ── 4. YOUTUBE IFRAME PLAYER API ───────────────────────────
  var ytPlayer = null;
  var lastSyncedSlide = -1;
  var userJustSeeked = false;   // brief lock after user clicks a slide

  window.onYouTubeIframeAPIReady = function() {
    ytPlayer = new YT.Player('yt-player', {
      videoId: '[VIDEO_ID]',    // ← replace with actual 11-char video ID
      playerVars: {
        autoplay: 0,
        controls: 1,
        rel: 0,
        modestbranding: 1,
        iv_load_policy: 3,
      },
      events: {
        onReady: function() {
          document.getElementById('chapter-label').textContent = 'Ready';
        }
      }
    });
  };

  // Load YouTube IFrame API dynamically
  var tag = document.createElement('script');
  tag.src = 'https://www.youtube.com/iframe_api';
  document.head.appendChild(tag);

  // ── 5. SYNC LOOP: polls getCurrentTime() every 500 ms ──────
  // Always running — handles play, pause, and seeks while paused.
  setInterval(function() {
    if (!ytPlayer || typeof ytPlayer.getCurrentTime !== 'function') return;
    if (userJustSeeked) return;

    var t = ytPlayer.getCurrentTime();

    // Find the highest-indexed slide whose startSec ≤ current time
    var targetIndex = 1;          // default: TOC slide
    var chapterTitle = 'Introduction';
    for (var i = 0; i < SLIDE_MAP.length; i++) {
      if (t >= SLIDE_MAP[i].startSec) {
        targetIndex = SLIDE_MAP[i].slideIndex;
        chapterTitle = SLIDE_MAP[i].title;
      }
    }

    // Update chapter bar
    document.getElementById('chapter-label').textContent = chapterTitle;
    var m = Math.floor(t / 60);
    var s = Math.floor(t % 60);
    document.getElementById('chapter-time').textContent =
      m + ':' + (s < 10 ? '0' : '') + s;

    // Navigate slides whenever target changes (playing or paused after a seek)
    if (targetIndex !== lastSyncedSlide) {
      lastSyncedSlide = targetIndex;
      Reveal.slide(targetIndex);
    }
  }, 500);

  // ── 6. REVERSE SYNC: clicking a slide → seeks video ────────
  Reveal.on('slidechanged', function(event) {
    var idx = event.indexh;
    var entry = SLIDE_MAP.find(function(e) { return e.slideIndex === idx; });
    if (entry && ytPlayer && typeof ytPlayer.seekTo === 'function') {
      userJustSeeked = true;
      ytPlayer.seekTo(entry.startSec, true);
      lastSyncedSlide = idx;
      // Re-enable sync after seek settles
      setTimeout(function() { userJustSeeked = false; }, 1500);
    }
  });

  // ── 6. SHARE BUTTONS ───────────────────────────────────────
  (function() {
    var relSlide = document.querySelector('.layout-related[data-yt-url]');
    if (!relSlide) return;
    var ytUrl   = relSlide.getAttribute('data-yt-url') || '';
    var ytTitle = relSlide.getAttribute('data-yt-title') || encodeURIComponent(document.title);
    var enc = encodeURIComponent;
    var emailBtn    = document.getElementById('share-email');
    var linkedinBtn = document.getElementById('share-linkedin');
    var xBtn        = document.getElementById('share-x');
    if (emailBtn)    emailBtn.href    = 'mailto:?subject=' + ytTitle + '&body=' + enc('Thought you might find this interesting: ' + ytUrl);
    if (linkedinBtn) linkedinBtn.href = 'https://www.linkedin.com/sharing/share-offsite/?url=' + enc(ytUrl);
    if (xBtn)        xBtn.href        = 'https://twitter.com/intent/tweet?url=' + enc(ytUrl) + '&text=' + ytTitle;
  })();
</script>
</body>
</html>
```

### Rules for filling the template

- Remove **all** placeholder comments and unused layout blocks from the final output
- Use only the `<section>` blocks that match the content you actually have
- Never use `layout-list` more than twice in a row — break it up with another layout type
- **Mandatory slides**: cover (index 0), toc (index 1), takeaways, related-videos (always last)
- **`SLIDE_MAP` array**: fill in every content slide's `slideIndex` and `startSec` from the Step 2 plan. Skip cover, toc, takeaways, and related. This is what drives both auto-advance and reverse-seek — do not omit it.
- **`[VIDEO_ID]`**: fill in once — in the YT.Player `videoId`. Must be the 11-character ID only.
- On the **cover slide**: fill in title, channel, duration, and thesis only — no thumbnail or video link.
- On the **TOC slide**: each `toc-item` uses `Reveal.slide(N)` with the correct 0-based slide index from the plan.
- On the **related slide**: use real YouTube URLs from Step 1b. Set `data-yt-url` to the full original URL for share buttons.
- For **layout-chart pie**: compute cumulative percentages for `conic-gradient`. Must sum to 100 — normalize if the speaker's numbers are approximate.
- For **layout-chart bar**: set each `bar-fill` width relative to the largest value (largest = 100%).
- Keep slide text terse: bullets 8–12 words, card descriptions 1 sentence, table cells 3–6 words.
- Language: always match the video's language. Do not translate unless the user explicitly asks.
- Font size: base is `18px` to fit content within the half-screen slide panel. Do not increase the base size.

---

## Output

Save to:
```
/sessions/.../mnt/outputs/[video-slug]-slides.html
```

Present with a `computer://` link and a 2–3 sentence note: what the video covered, how many slides, and one interesting thing you learned from it.

---

## Edge Cases

**No transcript:** Use description + title + any visible chapter markers. Note limitation to user.

**Dense/long video (> 90 min):** Cluster by theme, not by time. 5 strong thematic slides beat 25 chronological ones.

**Poor auto-caption quality:** Clean up filler and obvious errors; preserve speaker's meaning and phrasing.

**User requests a different language:** Ask once to confirm, then translate all slide content.

**Framework diagrams:** When a speaker introduces a named model (Golden Circle, 4 P's, Maslow's hierarchy, etc.), always use `layout-framework` for it — a visual representation communicates it better than bullets.
