# Proposal Generator (HubSpot + Google Docs)

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

When a HubSpot deal reaches your proposal stage, this pulls the deal, its line items and the main contact, fills a Google Docs template and posts the draft to Slack. After approval it emails the client a PDF and moves the deal to the next stage.

Built for agencies, consultancies and accounting firms that rebuild the same proposal by hand for every deal.

## What it does

1. **Deal Reached Proposal** receives `dealId` from a HubSpot workflow webhook. **Proposal Settings** holds the template, output folder, sender and next stage ID.
2. **Get Deal and Associations** calls the HubSpot API. **Has Line Items and Contact?** sends incomplete deals back to the rep via **Ask Rep to Fix Deal** instead of failing.
3. **Get Line Items** and **Get Primary Contact** fetch the details. **Build Proposal Data** (Code) formats the line items, total, dates and file name. **Contact Has Email?** guards the send.
4. **Copy Proposal Template** and **Fill Placeholders** create the client's document. **Approve Proposal** posts a link to the draft in `#proposals` and waits up to 3 days.
5. Approved: **Export as PDF**, **Email Proposal** with the PDF attached, **Move Deal to Proposal Sent**, **Confirm Sent**. On hold: **Note Proposal on Hold** keeps the draft for manual sending.
6. **On Workflow Error** posts any failure to `#automation-alerts` and logs it.

## Sample request

```bash
curl -X POST https://YOUR-N8N/webhook/proposal-ready \
  -H "Content-Type: application/json" -d '{"dealId":"4401"}'
```

Template placeholders: `{{client_name}}`, `{{client_company}}`, `{{deal_name}}`, `{{scope}}`, `{{line_items}}`, `{{total}}`, `{{proposal_date}}`, `{{valid_until}}`.

## Setup

1. Create a Google Docs template with the placeholders above and a folder for finished proposals. Put both IDs in **Proposal Settings**.
2. Set `sentStageId` to your pipeline's next stage ID and `hubspotPortalId` to your portal.
3. In a HubSpot workflow (deal enters proposal stage), add *Send a webhook* with `dealId` to the `/proposal-ready` URL.
4. Connect **HubSpot** (also on the three HTTP Request nodes), **Google Drive**, **Google Docs**, **Gmail** and **Slack**.

Every workflow ships inactive with credential placeholders. Connect your own accounts, run one test, then activate.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
    N0["Deal Reached Proposal<br/><small>webhook</small>"]
    N1["Proposal Settings<br/><small>set</small>"]
    N2["Get Deal and Associations<br/><small>httpRequest</small>"]
    N3["Has Line Items and Contact?<br/><small>if</small>"]
    N4["Get Line Items<br/><small>httpRequest</small>"]
    N5["Get Primary Contact<br/><small>httpRequest</small>"]
    N6["Build Proposal Data<br/><small>code</small>"]
    N7["Contact Has Email?<br/><small>if</small>"]
    N8["Copy Proposal Template<br/><small>googleDrive</small>"]
    N9["Fill Placeholders<br/><small>googleDocs</small>"]
    N10["Approve Proposal<br/><small>slack</small>"]
    N11["Approved?<br/><small>if</small>"]
    N12["Export as PDF<br/><small>googleDrive</small>"]
    N13["Email Proposal<br/><small>gmail</small>"]
    N14["Move Deal to Proposal Sent<br/><small>hubspot</small>"]
    N15["Confirm Sent<br/><small>slack</small>"]
    N16["Note Proposal on Hold<br/><small>slack</small>"]
    N17["Ask for Contact Email<br/><small>slack</small>"]
    N18["Ask Rep to Fix Deal<br/><small>slack</small>"]
    N19["On Workflow Error<br/><small>errorTrigger</small>"]
    N20["Format Error Details<br/><small>set</small>"]
    N21["Alert #automation-alerts<br/><small>slack</small>"]
    N22["Log to Error Sheet<br/><small>googleSheets</small>"]
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N3 --> N18
    N4 --> N5
    N5 --> N6
    N6 --> N7
    N7 --> N8
    N7 --> N17
    N8 --> N9
    N9 --> N10
    N10 --> N11
    N11 --> N12
    N11 --> N16
    N12 --> N13
    N13 --> N14
    N14 --> N15
    N19 --> N20
    N20 --> N21
    N20 --> N22
```
<!-- ARCHITECTURE:END -->
