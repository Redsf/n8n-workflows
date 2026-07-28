---
name: n8n-sticky-notes
description: >
  Rewrites sticky notes in n8n workflow JSON files to meet n8n community template
  publishing standards. Use this skill whenever a user uploads an n8n workflow JSON
  and asks to fix, update, improve, or add sticky notes — or when they receive an
  n8n community rejection email saying their sticky notes don't meet quality
  standards. Also trigger when the user says "prepare my workflow for publishing",
  "make my workflow template-ready", or "fix the annotations". This skill replaces
  all existing sticky notes with a compliant set: one large Main Overview sticky
  plus 3–4 colored section stickies that act as visual backgrounds behind node
  clusters. Never skip this skill for any n8n JSON sticky note task.
---

# n8n Sticky Notes — Community Template Standard

Rewrites sticky notes in n8n workflow JSON to meet the n8n community publishing
guidelines. Produces exactly the structure that passes the n8n template review.

---

## The Standard (what n8n requires)

Every published template must have **two types** of sticky note — nothing else:

### Type 1 — Main Overview (exactly 1 per workflow)
- **Color:** `7` (grey) — this color is reserved for the Overview only
- **Position:** To the left of all nodes, not overlapping anything
- **Size:** `width: 520–580`, `height: 700–920` (scale to workflow complexity)
- **Content — fixed 3-section structure:**

```
## [emoji] [Workflow Name]

[1–2 sentences: what the workflow does end-to-end]

**Perfect for:** [specific job role or team who would use this]

---

## How it works

1. **[Node Name]** — [what it does, one sentence]
2. **[Node Name]** — [what it does, one sentence]
... (cover EVERY node in execution order, including branches and optional paths)

---

## Setup (~X minutes)

1. **[Service/Credential]** — [exact action, name the specific node in italics]
2. **[Service/Credential]** — [exact action, name the specific node in italics]
...
> [Any warnings, file format notes, cost warnings, or important caveats]
```

### Type 2 — Section stickies (3–4 per workflow)
- **Purpose:** Visual background containers that sit *behind* node clusters
- **Color:** See color map below — one color per logical stage
- **Position:** Slightly larger than the node cluster they cover (~80–100px padding)
- **Content — fixed 2-part structure:**

```
## [N]️⃣ [Section Name]

[2–4 sentences in plain prose describing what this cluster of nodes does.
Reference specific node names in **bold**. No bullet points. No sub-headers.]
```

---

## Color Map (use consistently)

| Color code | Meaning | When to use |
|---|---|---|
| `7` (grey) | Main Overview | Overview sticky ONLY — never sections |
| `5` (blue) | Trigger / Intake | Section 1: form, trigger, download, fetch |
| `3` (green) | Core logic / AI | Section 2: AI agent, processing, filtering |
| `6` (orange) | Secondary processing | Section 3: extraction, rewriting, transformation |
| `4` (purple) | Output / Logging | Section 4: emails, Slack, Sheets, final log |

> If a workflow has only 3 sections, use colors `5`, `3`, `6`. Skip `4`.

---

## Step-by-Step Process

### Step 1 — Parse node positions

Read every node's `position: [x, y]` from the JSON. Build a mental map:

- What is the leftmost x? (used to place Overview)
- What is the top-most y? (used for section vertical placement)
- Which nodes cluster together spatially AND logically?

### Step 2 — Trace the execution flow

Follow `connections` from the trigger node to the end. Note:
- Trigger type (form, schedule, webhook, Drive, manual)
- Every node name and its role
- Any branch points (If nodes), loops (SplitInBatches), optional paths
- All external services (Gmail, Slack, Sheets, Drive, OpenAI, Groq, Apify, etc.)
- Error handlers if present

### Step 3 — Delete all existing sticky notes

Remove every node where `"type": "n8n-nodes-base.stickyNote"` from the nodes array.
Also remove their IDs from any connections (sticky notes are never in connections,
but confirm).

Non-compliant patterns to always delete:
- Separate "Overview" + "Setup" sticky pair
- Small floating "Step 1 / Step 2 / Step 3" labels
- Any sticky not visually backed behind a node cluster
- Any sticky using color `7` for a section (grey = Overview only)

### Step 4 — Group nodes into 3–4 sections

Identify logical stages. Common groupings:

| Stage name | Typical nodes |
|---|---|
| Trigger & Intake | Form trigger, webhook, schedule, download, fetch, validate |
| AI / Core Logic | AI agent, LLM model, code nodes, classification, filtering |
| Processing | Extraction, rewriting, transformation, aggregation, looping |
| Output & Logging | Email, Slack, Sheets, Drive upload, execution log, error handler |

> A workflow with a single linear path usually needs 3 sections.
> A workflow with branches, loops, or dual AI stages needs 4 sections.

### Step 5 — Calculate sticky positions

**Main Overview position:**
```
x = leftmost_node_x - 640
y = (topmost_node_y + bottommost_node_y) / 2 - 420
```

**Section sticky position (per group):**
```
x = leftmost_node_in_group - 100
y = topmost_node_in_group - 160
width  = (rightmost_node_x - leftmost_node_x) + 360
height = (bottommost_node_y - topmost_node_y) + 360
```

Minimum section dimensions: `width: 300`, `height: 260`

### Step 6 — Write the Main Overview sticky

Follow the exact 3-section template above. Rules:
- List **every** node in "How it works" — no skipping, no grouping
- Name optional/branching paths explicitly: `*(optional path)*`
- In Setup, always name the exact node in *italics* where the user must act
- Estimate setup time honestly: `~5 min` for 1–2 credentials, `~15 min` for 4+
- Use `>` blockquote for warnings (file size limits, API costs, ToS notices)

### Step 7 — Write the section stickies

One sticky per section group. Rules:
- Title uses number emoji: `1️⃣`, `2️⃣`, `3️⃣`, `4️⃣`
- Body is **prose only** — no bullets, no numbered lists, no sub-headers
- 2–4 sentences maximum
- Bold the specific node names being described
- Describe *what* the cluster does, not *how* to configure it (setup belongs in Overview)

### Step 8 — Assemble the final JSON

Add all new sticky nodes to the `nodes` array. Preserve every existing non-sticky
node exactly as-is — change nothing in their `parameters`, `credentials`,
`connections`, `position`, or any other field.

Output the complete valid JSON with all original nodes intact plus the new stickies.

---

## Positioning Quick Reference

```
CANVAS LAYOUT (left → right):

[Main Overview]   [Section 1 bg]   [Section 2 bg]   [Section 3 bg]   [Section 4 bg]
                  [ node  node ]   [ node  node ]   [  node  node]   [  node  node]
                  [ node       ]   [ node       ]   [  node      ]   [  node      ]
```

The Main Overview never overlaps any section. Section backgrounds sit *behind*
(lower z-order) their nodes — in n8n this is achieved purely by position, the nodes
render on top automatically.

---

## Content Quality Rules

**Main Overview — "How it works" list**
- ✅ `1. **Onboarding Form** — Collects new hire name, email, role, department, start date, and manager details.`
- ❌ `1. Form — Gets data` (too vague)
- ❌ `1. **Step 1** — Form submission` (don't use step numbers as names)

**Main Overview — "Setup" list**
- ✅ `1. **Groq API** — Add your key in the *Generate AI Content* node.`
- ❌ `1. Add Groq API key` (doesn't say where)
- ❌ `1. Groq — Connect` (not specific enough)

**Section sticky body**
- ✅ `The **Onboarding Form** collects all new hire details. The **AI Agent** (Groq Llama 3.3 70B) generates every piece of communication in a single structured call, enforced by the **Structured Output Parser**.`
- ❌ `- Form collects data\n- AI generates emails\n- Parser validates output` (no bullets)
- ❌ `This section handles the first part of the workflow.` (too vague, no node names)

---

## Sticky Node JSON Template

```json
{
  "id": "sticky-[descriptive-id]",
  "name": "[Human-readable name]",
  "type": "n8n-nodes-base.stickyNote",
  "typeVersion": 1,
  "position": [x, y],
  "parameters": {
    "color": 7,
    "width": 560,
    "height": 800,
    "content": "## Workflow Name\n\n..."
  }
}
```

Note: sticky notes have no `connections` entries. Do not add them to `connections`.

---

## Common Mistakes to Avoid

| Mistake | Correct approach |
|---|---|
| Two stickies: one "Overview", one "Setup" | Merge into a single Main Overview |
| "Step 1 / Step 2 / Step 3" floating labels | Replace with full section backgrounds |
| Section sticky using color `7` | Color `7` is Overview only; use `5/3/6/4` for sections |
| Section sticky floating away from nodes | Position so it visually contains the nodes |
| Leaving original non-compliant stickies in JSON | Delete all old stickies before adding new ones |
| Setup instructions inside a section sticky | Setup belongs only in the Main Overview |
| Bullet lists inside section sticky body | Prose only in section stickies |
| Skipping error handler nodes in "How it works" | List every node including error/disabled ones |
