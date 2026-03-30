# youtube-to-slides

> A [Claude Code](https://claude.ai/claude-code) skill that turns any YouTube video into a beautiful, interactive slide deck — with the video and slides synced side by side.

[![Claude Skill](https://img.shields.io/badge/Claude-Skill-5C8A6B?logo=anthropic&logoColor=white)](https://claude.ai/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

Paste a YouTube URL. Get a polished HTML presentation where:

- **Left panel** — the YouTube video plays in-page
- **Right panel** — slides auto-advance in sync as the video plays
- **Click any slide** — the video jumps to that exact moment

The output is a single self-contained `.html` file you can open in any browser, share with a link, or host anywhere.

![Demo screenshot](assets/demo.png)
<!-- Replace with an actual screenshot or GIF once you have one -->

---

## Features

| Feature | Detail |
|---|---|
| 🎬 **Video + slides side by side** | Split-screen layout; YouTube IFrame Player API for native sync |
| ⏱ **Auto-advance** | Slides advance automatically as the video plays through sections |
| 🔁 **Reverse seek** | Click any slide to jump the video to that moment |
| 📋 **Table of contents** | Second slide lists every section with clickable jump links |
| 🎨 **10 smart layouts** | Lists, quotes, two-column, stats, grid cards, tables, framework diagrams, CSS pie/bar charts |
| 📊 **CSS-only charts** | Pie (conic-gradient) and bar charts — no chart library needed |
| 🌐 **Multi-language** | Slides match the video's language automatically |
| 🔗 **Share buttons** | Email, LinkedIn, and X share on the final slide |
| 📺 **No API key needed** | Transcripts fetched via `youtube-transcript-api` |

---

## Installation

### In Claude Code

1. Download `youtube-to-slides.skill` from [Releases](../../releases)
2. In your terminal, run:
   ```
   claude
   ```
3. In the Claude Code chat, say:
   ```
   Install this skill: /path/to/youtube-to-slides.skill
   ```

### Manual install (Claude Code)

Clone this repo into your Claude skills directory:

```bash
git clone https://github.com/YOUR_USERNAME/youtube-to-slides ~/.claude/skills/youtube-to-slides
```

---

## Usage

Once installed, just give Claude a YouTube URL and tell it what you want:

```
帮我把这个视频做成slides：https://www.youtube.com/watch?v=B26CwKm5C1k
```

```
Turn this into a slide deck: https://www.youtube.com/watch?v=iG9CE55wbtY
```

```
Summarize this video for my team: https://youtu.be/qp0HIF3SfI4
```

Claude will:
1. Fetch the transcript (auto-installs `youtube-transcript-api` if needed)
2. Analyze the content and plan a slide structure
3. Generate a single `.html` file in your output folder

> **Note:** Transcript extraction requires internet access to YouTube. Works best in Claude Code on your local machine. Claude Cowork's VM may have network restrictions that block YouTube.

---

## Output structure

Every generated deck follows this structure:

```
Slide 0  →  Cover (title, channel, duration, thesis, thumbnail)
Slide 1  →  Table of Contents (all sections, clickable, with timestamps)
Slide 2+ →  Content slides (layout chosen to match content shape)
Slide N-1 → Takeaways
Slide N  →  Related videos + share buttons
```

### Layout selection logic

The skill picks the best visual form for each piece of content:

```
Quote or key insight?              → Full-screen blockquote
Percentage breakdown?              → CSS pie/donut chart
Quantities across categories?      → Horizontal bar chart
Two things compared (no numbers)?  → Two-column split
Single striking number?            → Giant stat
Named conceptual model/framework?  → CSS diagram (pyramid, circles, flow)
3–4 parallel concepts with labels? → Card grid
3+ things with multiple attributes?→ Table
Otherwise                          → Bullet list
```

---

## How it works

```
YouTube URL
    │
    ▼
fetch_transcript.py
    │  youtube-transcript-api (no API key)
    │  YouTube oEmbed (title, channel)
    │
    ▼
Claude analyzes transcript
    │  Extracts thesis, arc, sections, key claims,
    │  frameworks, quotes, data points
    │  Plans slides + SLIDE_MAP timestamp array
    │
    ▼
HTML generation
    │  Reveal.js 4.6.1 (embedded mode)
    │  YouTube IFrame Player API
    │  CSS-only charts + diagrams
    │  DM Serif Display + Inter (Google Fonts)
    │
    ▼
output.html  ←  single self-contained file
```

### Sync mechanism

```javascript
// Every 500ms while playing:
player.getCurrentTime() → look up SLIDE_MAP → Reveal.slide(N)

// When user clicks a slide:
Reveal.on('slidechanged') → player.seekTo(startSec)
```

---

## Repo structure

```
youtube-to-slides/
├── SKILL.md                  # Claude skill instructions (the "brain")
├── scripts/
│   └── fetch_transcript.py   # Transcript + metadata fetcher
├── evals/
│   └── evals.json            # Test cases for the skill
├── assets/
│   └── demo.png              # Screenshot for README
└── README.md
```

---

## Requirements

- **Claude Code** (or Claude Cowork desktop app)
- **Python 3.8+** with internet access (for transcript extraction)
- A browser that can reach YouTube (for the generated slide page)

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Ideas for improvements:
- [ ] Support for YouTube playlists (one deck per video or one combined deck)
- [ ] Light mode theme toggle
- [ ] Export to PPTX
- [ ] Custom branding / color themes
- [ ] Chapter markers from YouTube chapters

---

## License

[MIT](LICENSE) © 2025
