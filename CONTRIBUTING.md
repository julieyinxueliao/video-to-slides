# Contributing to youtube-to-slides

Thank you for wanting to improve this skill! Here's everything you need to get started.

---

## How the skill works

This is a **Claude Code skill** — a set of instructions in `SKILL.md` that Claude follows when a user pastes a YouTube URL. The skill is not a traditional application; Claude itself is the runtime.

The only executable code is `scripts/fetch_transcript.py`, which fetches the transcript and metadata before Claude generates the HTML.

---

## Ways to contribute

### 1. Improve the SKILL.md instructions

`SKILL.md` is the heart of the skill. It tells Claude how to:
- Structure content into slides
- Choose the right layout for each piece of content
- Generate the HTML + JavaScript

Good contributions here:
- Add new layout types (e.g., timeline, numbered steps, image+caption)
- Improve the decision heuristic for layout selection
- Add better examples in the template
- Improve the CSS design system

**Workflow:** Edit `SKILL.md` → reinstall the skill → test with a few videos → open a PR with before/after examples.

### 2. Improve the transcript fetcher

`scripts/fetch_transcript.py` handles transcript extraction. Improvements welcome:
- Better language detection / fallback logic
- Support for alternative transcript APIs (for when `youtube-transcript-api` is blocked)
- Richer metadata extraction (chapters, description, likes)

### 3. Add or improve evals

`evals/evals.json` contains test cases. Good evals make it easier to verify that changes don't break existing behavior.

To add an eval:
```json
{
  "id": 3,
  "prompt": "Your test prompt with a YouTube URL",
  "expected_output": "Describe what a good output looks like",
  "files": [],
  "assertions": [
    {
      "name": "assertion_name",
      "description": "What to check in the output"
    }
  ]
}
```

### 4. Report bugs or suggest features

Open a GitHub Issue. Include:
- The YouTube URL you tested with
- What happened vs. what you expected
- Any error messages from the Claude Code session

---

## Development setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/youtube-to-slides
cd youtube-to-slides

# Install the skill into Claude Code for local testing
# (copy the directory to your Claude skills folder, or use a symlink)
ln -s $(pwd) ~/.claude/skills/youtube-to-slides

# Test the transcript fetcher directly
python scripts/fetch_transcript.py "https://www.youtube.com/watch?v=iG9CE55wbtY"
```

---

## Pull request guidelines

- **One change per PR.** Avoid bundling layout changes with fetcher changes.
- **Include a test video.** In your PR description, link to a YouTube video where you verified the change looks correct.
- **Show before/after.** If you're changing the visual output, include screenshots of the old and new slide output.
- **Don't break existing layouts.** Run through at least 2–3 different videos to check nothing regressed.

---

## Code style

- Python: follow PEP 8, use type hints where practical
- HTML/CSS in SKILL.md: keep consistent with the existing design system variables (`--bg`, `--accent`, etc.)
- No external dependencies beyond `youtube-transcript-api` and standard library

---

## Questions?

Open a GitHub Discussion or Issue. Happy to help!
