---
name: n8n-linkedin-caption
description: Write a single, polished, Top 1% LinkedIn caption from an uploaded n8n workflow — whether provided as a JSON file or a screenshot. Use this skill whenever the user uploads anything related to an n8n workflow AND asks for a LinkedIn post, caption, or write-up. Trigger even if they say something casual like "write a post about this workflow," "make a LinkedIn caption," or "help me post this." The output targets Marketing & Growth professionals and follows a strict, research-backed formula for maximum reach and engagement.
---

# n8n LinkedIn Caption Writer

Turns an n8n workflow (JSON or screenshot) into a single, polished, Top 1% LinkedIn caption for a Marketing & Growth audience.

---

## Step 1 — Understand the Workflow Input

The user will provide one of:
- **JSON file** — uploaded from n8n's "Export Workflow" feature
- **Screenshot** — an image of the n8n canvas

### If JSON:
Read the file. Extract:
- Workflow name
- Nodes used (especially integrations: Gmail, Slack, Airtable, OpenAI, Sheets, etc.)
- Trigger type (webhook, schedule, manual, etc.)
- The logical flow: what goes in → what happens → what comes out
- Any conditional logic or loops that signal sophistication

### If Screenshot:
Study the image carefully. Identify:
- Visible node names and their icons
- The left-to-right flow of the automation
- Any labels, notes, or titles visible on the canvas

---

## Step 2 — Ask 1–2 Clarifying Questions

Before writing, ask the user **exactly 1 or 2** of the most impactful clarifying questions. Pick from this list based on what you couldn't infer from the workflow:

1. **The Result:** "What result does this automation actually produce for you? (e.g., saves 3 hours/week, reduced churn by 12%, generates 50 leads/month)"
2. **The Origin Story:** "What was the manual pain or problem this replaced?"
3. **The Hook Angle:** "Do you want to lead with the time saved, the revenue impact, or the 'wow' of the tech stack?"
4. **Personal tone:** "Should the caption sound more like a founder sharing a win, or a growth expert teaching a lesson?"

Do not ask all four. Pick only what you genuinely need. If the workflow is detailed enough, one question is fine.

---

## Step 3 — Write the Caption

Apply the full caption formula from `references/caption-rules.md`.

### Output Format:
```
[CAPTION]

---
Hook Type Used: [e.g., Contrarian Hook]
Framework Used: [e.g., PAS]
CTA Type: [e.g., Low Friction Question]
Estimated Read Time: [e.g., ~45 seconds]
```

Always show the caption first, followed by the small metadata block so the user understands what strategy was applied.

---

## Reference Files

- `references/caption-rules.md` — Full LinkedIn caption rulebook (rules from user + additional research-backed rules). **Read this before writing any caption.**
