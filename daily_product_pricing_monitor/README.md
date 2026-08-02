# Daily Product Pricing Monitor

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

A scheduled competitive-pricing watchdog that reads a product catalog from Google Sheets, looks up live competitor prices for each item via Google Shopping, flags products that are priced too high or too low against the market, and sends a daily summary report by Slack and email.

Built for e-commerce and retail teams who need to catch pricing drift against competitors every morning without manually shopping around for every SKU.

## What it does

1. **Schedule Trigger** runs daily at 8 AM.
2. **Get products from sheets** (Google Sheets) reads the full product catalog.
3. **Clear Memory and Normalize Columns** (Code) resets the workflow's accumulated pricing results and normalizes inconsistent column names (`product_name`/`Product Name`/`name`, etc.) into a consistent shape: `productName`, `yourPrice`, `sku`, `category`, `brand`.
4. **Loop Through Each Product** (Split In Batches) processes the catalog one product at a time, looping back after each product is logged, and routing to the summary step once the batch is exhausted.
5. **Prepare Search Query** (Code) builds a search string from brand, product name and SKU.
6. **Search Google Shopping Prices** (HTTP Request to SearchAPI.io's `google_shopping` engine) fetches live competitor listings for that query.
7. **Analyze Pricing Gap** (Code) parses the shopping results, computes the lowest and average competitor price, calculates the percentage gap against `yourPrice`, classifies severity (`ok` / `warning` at ±10% / `critical` at ±20%), and suggests a price 3% below the lowest competitor.
8. **Save Result to Memory** (Code) appends each product's analysis to workflow static data so results accumulate across the loop.
9. **Filter Critical or Warning Alerts** only passes through products where `severity != "ok"`.
10. **Send Slack Pricing Alert** posts a per-product alert (your price, lowest competitor, gap %, suggested price) to a Slack channel.
11. **Log to Price History Sheet** (Google Sheets append) records every analyzed product — including ones marked "ok" — to a historical pricing log.
12. **Continue to Next Product** (NoOp) loops back to **Loop Through Each Product** for the next item.
13. Once all products are processed, **Build Daily Summary Report** (Code) reads the full accumulated results from static data and builds both an HTML report table (color-coded by severity) and a condensed Slack summary message.
14. **Email Daily Report** (Gmail) sends the HTML report.
15. **Send a message** (Slack) posts the condensed summary to a general channel.

## Setup (about 15 minutes)

1. **Google Sheets** — connect Google Sheets OAuth2 in **Get products from sheets** (catalog, ID `1axRTQelNLar_LC2m3Mul9wKJVHYhqEtie9lC4FR1w2c`) and **Log to Price History Sheet** (history log, ID `1zMSlJ3YHlkffZ_V0m1pS_HG12jhxNMRInG7QioQxgNQ`). Replace both spreadsheet IDs with your own sheets.
2. **SearchAPI.io** — replace the `YOUR_SEARCHAPI_KEY` placeholder in **Search Google Shopping Prices** with your own key. Move it into an n8n credential rather than a hardcoded query parameter if you plan to share this workflow further.
3. **Slack** — connect Slack OAuth2 in **Send Slack Pricing Alert** (channel `pricing-alerts`, ID `C0AK5VBUE1Z`) and **Send a message** (channel `all-general-all-department`, ID `C0AK1R8LT3M`). Update both channel IDs to your own workspace.
4. **Gmail** — connect Gmail OAuth2 in **Email Daily Report** and replace the hardcoded recipient `alerts@example.com` with your real distribution address.

## Error handling

There is no dedicated error-handling branch (no Error Trigger or retry/notify-on-failure logic) in this workflow — a failed HTTP call to SearchAPI or a malformed sheet row will fail the run rather than degrade gracefully. Consider adding continue-on-fail to **Search Google Shopping Prices** so one bad product doesn't stop the whole batch.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
    N0["Clear Memory and Normalize Columns<br/><small>code</small>"]
    N1["Loop Through Each Product<br/><small>splitInBatches</small>"]
    N2["Prepare Search Query<br/><small>code</small>"]
    N3["Search Google Shopping Prices<br/><small>httpRequest</small>"]
    N4["Analyze Pricing Gap<br/><small>code</small>"]
    N5["Save Result to Memory<br/><small>code</small>"]
    N6{{"Filter Critical or Warning Alerts<br/><small>filter</small>"}}
    N7["Send Slack Pricing Alert<br/><small>slack</small>"]
    N8["Continue to Next Product<br/><small>noOp</small>"]
    N9["Build Daily Summary Report<br/><small>code</small>"]
    N10["Email Daily Report<br/><small>gmail</small>"]
    N11["Get products from sheets<br/><small>googleSheets</small>"]
    N12["Send a message<br/><small>slack</small>"]
    N13["Log to Price History Sheet<br/><small>googleSheets</small>"]
    N14(["Schedule Trigger<br/><small>scheduleTrigger</small>"])
    N0 --> N1
    N1 -->|done| N9
    N1 -->|loop| N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N5 --> N6
    N6 --> N7
    N7 --> N13
    N8 --> N1
    N9 --> N10
    N9 --> N12
    N11 --> N0
    N13 --> N8
    N14 --> N11

    class N14 trigger
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
