# AI Sales Meeting Prep via WhatsApp (Apify)

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

An hourly meeting-prep assistant that checks Google Calendar for meetings starting soon, researches each attendee's last email thread and LinkedIn activity, and sends a casual pre-meeting briefing to WhatsApp — bullet points on what was last discussed and fresh talking points, so the user never walks into a call cold.

Built for salespeople, founders, or consultants who take a lot of external meetings and want a five-second phone glance to replace ten minutes of manual digging through Gmail and LinkedIn before every call.

## What it does

**Main flow (calendar polling):**

1. **Schedule Trigger** runs hourly.
2. **Check For Upcoming Meetings** (Google Calendar, `getAll`, limited to 1) looks for the next event starting within the coming hour on a specific calendar (`n8n-events`).
3. **Extract Attendee Information** (LangChain Information Extractor, backed by **OpenAI Chat Model2**) parses the meeting's description/attendee list into a structured array of `{name, email, linkedin_url}` — it's designed to pick up LinkedIn URLs and names embedded in the invite's free-text description, since Google Calendar invites don't carry that natively.
4. **Attendees to List** splits the array into one item per attendee, then fans out into two parallel sub-workflow calls per attendee (self-calling this same workflow by `$workflow.id`):
   - **Set Route Email** tags the item `route: "email"` → **Get Correspondance** (Execute Workflow, mode `each`) re-enters this workflow's **Execute Workflow Trigger** → **Router**.
   - **Set Route Linkedin** tags the item `route: "linkedin"` → **Get LinkedIn Profile & Activity** (Execute Workflow, mode `each`) does the same.
5. **Merge** joins the email-summary and LinkedIn-summary results back together per attendee, **Merge Attendee with Summaries** combines them onto the attendee record, and **Aggregate Attendees** collapses everything into a single item holding an `attendees` array.
6. **Attendee Research Agent** (LLM chain, **OpenAI Chat Model3**) writes the actual briefing: meeting time/link/summary plus, per attendee, their last correspondence and LinkedIn talking points, in a casual SMS-style tone with bullet points.
7. **WhatsApp Business Cloud** sends the generated text to a fixed recipient number.

**Attendee Researcher sub-workflow (same file, entered via Execute Workflow Trigger):**

8. **Execute Workflow Trigger** → **Router** (switch on `route`) splits into two branches that never run together:
   - **Email branch:** **Has Email Address?** → **Get Last Correspondence** (Gmail, filtered by the attendee's email) → **Has Emails?** → **Get Message Contents** → **Simplify Emails** → **Correspondance Recap Agent** (LLM chain, **OpenAI Chat Model**) condenses the thread into a short recap → **Return Email Success**. Missing address or no emails found short-circuit to error nodes.
   - **LinkedIn branch:** **Has LinkedIn URL?** → **Set LinkedIn Cookie** (injects a hardcoded LinkedIn session cookie) → **APIFY Web Scraper** (HTTP request to Apify's `apify~web-scraper` actor, impersonating the user's own logged-in LinkedIn session) → **Is Scrape Successful?** → a chain of HTML-extraction nodes (**Extract Profile Metadata**, **Sections To List**, **Get About Section**/**Get Activity Section**, **Extract About**/**Extract Activities**, **Activities To List**, **Get Activity Details**, **Activities To Array**) pulls the profile's About and recent Activity sections → **Merge1** joins them → **LinkedIn Summarizer Agent** (LLM chain, **OpenAI Chat Model1**) writes a short "recent activity" summary → **Return LinkedIn Success**. A missing URL or failed scrape short-circuits to error nodes.

## Sample input

There's no webhook — the workflow is entirely schedule- and calendar-driven. The trigger event is simply a Google Calendar event containing attendee context in its description, e.g.:

```
Summary: Renewal call - Acme Corp
Description: Quarterly renewal discussion with Jane Doe (jane@acmecorp.com, linkedin.com/in/janedoe)
Attendees: jane@acmecorp.com, you@yourcompany.com
Start: 2026-07-08T15:00:00Z
Hangout Link: https://meet.google.com/abc-defg-hij
```

The final WhatsApp message reads roughly like a friendly text: "Heads up — call with Jane at 3pm today (link). Last time you two talked about the Q2 renewal terms... Jane's been posting about..." etc.

## Setup (~45 minutes)

1. **Google Calendar** — add `googleCalendarOAuth2Api` to **Check For Upcoming Meetings**, and replace the hardcoded calendar ID (`c_5792bdf...@group.calendar.google.com`, cached as "n8n-events") with your own calendar.
2. **OpenAI** — add `openAiApi` to **OpenAI Chat Model**, **OpenAI Chat Model1**, **OpenAI Chat Model2**, and **OpenAI Chat Model3** (used respectively by the email recap agent, LinkedIn summarizer, attendee information extractor, and the final briefing writer).
3. **Gmail** — add `gmailOAuth2` to **Get Last Correspondence** and **Get Message Contents** so the email branch can search and read the attendee's last thread.
4. **Apify** — add an `httpQueryAuth` credential ("Apify API") to **APIFY Web Scraper**. This uses Apify's generic `web-scraper` actor (not a purpose-built LinkedIn scraper) driven by a custom `pageFunction`, so no extra actor setup is needed beyond an Apify account and API token.
5. **LinkedIn session cookie (critical, hardcoded placeholder)** — **Set LinkedIn Cookie** has a literal `<COPY_YOUR_LINKEDIN_COOKIES_HERE>` placeholder for `linkedin_cookies`; you must paste your own `li_at` session cookie value here for the scraper to authenticate as you. This risks violating LinkedIn's Terms of Service — consider using a secondary/throwaway account rather than your primary one.
6. **WhatsApp Business Cloud** — add `whatsAppApi` to **WhatsApp Business Cloud**, and replace the hardcoded `phoneNumberId` (`477115632141067`) and `recipientPhoneNumber` (`44123456789`) with your own sender ID and recipient.
7. **Self-referencing sub-workflow** — **Get Correspondance** and **Get LinkedIn Profile & Activity** both call `{{ $workflow.id }}` (this same workflow) via its **Execute Workflow Trigger**. Don't duplicate or re-import this workflow under a new ID without also checking those references still resolve.
8. Tune the **Schedule Trigger** interval and the `timeMax`/`timeMin` window in **Check For Upcoming Meetings** (currently "next hour") to match how far ahead you want your heads-up notification.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["Execute Workflow Trigger"]
        N0["Get Message Contents<br/><small>gmail</small>"]
        N1["Simplify Emails<br/><small>set</small>"]
        N5(["Execute Workflow Trigger<br/><small>executeWorkflowTrigger</small>"])
        N6["OpenAI Chat Model<br/><small>lmChatOpenAi</small>"]
        N7["Get Last Correspondence<br/><small>gmail</small>"]
        N8["OpenAI Chat Model1<br/><small>lmChatOpenAi</small>"]
        N12["Return LinkedIn Success<br/><small>set</small>"]
        N13["Return LinkedIn Error<br/><small>set</small>"]
        N14["Return Email Error<br/><small>set</small>"]
        N15["Return Email Success<br/><small>set</small>"]
        N18{{"Router<br/><small>switch</small>"}}
        N19["Return LinkedIn Error1<br/><small>set</small>"]
        N20{{"Has Emails?<br/><small>if</small>"}}
        N21["Return Email Error1<br/><small>set</small>"]
        N22["Sections To List<br/><small>splitOut</small>"]
        N23["Set LinkedIn Cookie<br/><small>set</small>"]
        N26{{"Has Email Address?<br/><small>if</small>"}}
        N27{{"Has LinkedIn URL?<br/><small>if</small>"}}
        N31["Activities To Array<br/><small>aggregate</small>"]
        N32["Extract Profile Metadata<br/><small>html</small>"]
        N33["Activities To List<br/><small>splitOut</small>"]
        N34["APIFY Web Scraper<br/><small>httpRequest</small>"]
        N35["Get Activity Details<br/><small>html</small>"]
        N36["Get Sections<br/><small>html</small>"]
        N37["Get About Section<br/><small>set</small>"]
        N38["Get Activity Section<br/><small>set</small>"]
        N39["Extract Activities<br/><small>html</small>"]
        N40["Merge1<br/><small>merge</small>"]
        N41{{"Is Scrape Successful?<br/><small>if</small>"}}
        N42["Extract About<br/><small>html</small>"]
        N44["Correspondance Recap Agent<br/><small>chainLlm</small>"]
        N46["LinkedIn Summarizer Agent<br/><small>chainLlm</small>"]
    end
    subgraph G1 ["Schedule Trigger"]
        N2["Check For Upcoming Meetings<br/><small>googleCalendar</small>"]
        N3["OpenAI Chat Model2<br/><small>lmChatOpenAi</small>"]
        N4["Extract Attendee Information<br/><small>informationExtractor</small>"]
        N9["OpenAI Chat Model3<br/><small>lmChatOpenAi</small>"]
        N10["WhatsApp Business Cloud<br/><small>whatsApp</small>"]
        N11(["Schedule Trigger<br/><small>scheduleTrigger</small>"])
        N16["Set Route Email<br/><small>set</small>"]
        N17["Set Route Linkedin<br/><small>set</small>"]
        N24["Attendees to List<br/><small>splitOut</small>"]
        N25["Merge Attendee with Summaries<br/><small>set</small>"]
        N28["Get Correspondance<br/><small>executeWorkflow</small>"]
        N29["Merge<br/><small>merge</small>"]
        N30["Aggregate Attendees<br/><small>aggregate</small>"]
        N43["Get LinkedIn Profile &amp; Activity<br/><small>executeWorkflow</small>"]
        N45["Attendee Research Agent<br/><small>chainLlm</small>"]
    end
    N29 --> N25
    N40 --> N46
    N18 -->|email| N26
    N18 -->|linkedin| N27
    N20 -->|true| N0
    N20 -->|false| N14
    N36 --> N37
    N36 --> N38
    N42 --> N40
    N16 --> N28
    N1 --> N44
    N11 --> N2
    N22 --> N36
    N34 --> N41
    N24 --> N16
    N24 --> N17
    N37 --> N42
    N27 -->|true| N23
    N27 -->|false| N19
    N33 --> N35
    N39 --> N33
    N28 --> N29
    N26 -->|true| N7
    N26 -->|false| N21
    N17 --> N43
    N31 --> N40
    N30 --> N45
    N23 --> N34
    N35 --> N31
    N38 --> N39
    N0 --> N1
    N41 -->|true| N32
    N41 -->|false| N13
    N45 --> N10
    N7 --> N20
    N5 --> N18
    N32 --> N22
    N46 --> N12
    N44 --> N15
    N2 --> N4
    N4 --> N24
    N25 --> N30
    N43 --> N29
    N6 -.languageModel.-> N44
    N8 -.languageModel.-> N46
    N3 -.languageModel.-> N4
    N9 -.languageModel.-> N45

    class N5,N11 trigger
    class N3,N6,N8,N9 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
