# Referral Tracking & Rewards

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

Captures referrals, thanks the referrer, logs everything in a tracker sheet, and when the referred lead becomes a client it asks finance to send the reward and tells the referrer the good news. Nobody is rewarded twice.

Built for referral-driven firms (CPAs, advisors, agencies, contractors) that track referrals in someone's head or an inbox.

## What it does

1. **New Referral** receives the form. **Referral Settings** holds the sender and reward text. **Normalize Referral** cleans both emails.
2. **Valid Referral?** requires both emails and blocks self-referrals (400 otherwise). **Confirm Referral** answers the form.
3. **Find Referrer in HubSpot** looks up the referrer. **Save Referred Lead** upserts the new lead with `referred_by_email`.
4. **Referrer in CRM?** decides whether **Thank the Referrer** emails them. **Log Referral** writes the row (status `referred`) and **Announce Referral** posts to `#referrals`.
5. **Deal Won** receives the client's email from a HubSpot workflow. **Find Open Referral** looks for a row still marked `referred`.
6. **Was a Referral?** runs **Ask Finance to Send Reward**, **Tell Referrer the Good News** and **Mark Reward Sent**, which changes the status so the reward cannot fire again.
7. **On Workflow Error** posts any failure to `#automation-alerts` and logs it.

## Sample request

```bash
curl -X POST https://YOUR-N8N/webhook/referral \
  -H "Content-Type: application/json" \
  -d '{"firstName":"Marcus","lastName":"Lee","email":"marcus@leewealth.com","company":"Lee Wealth Partners","referredByEmail":"dana@whitfieldcpa.com","note":"Dana said you fixed their intake process"}'

curl -X POST https://YOUR-N8N/webhook/referral-deal-won \
  -H "Content-Type: application/json" \
  -d '{"contactEmail":"marcus@leewealth.com","dealName":"Lee Wealth - Onboarding automation","amount":"9000"}'
```

## Setup

1. In HubSpot, create a contact property `referred_by_email` (single-line text).
2. Create a **Referral Tracker** sheet with headers: `receivedAt, leadEmail, leadName, leadCompany, referrerEmail, referrerName, referrerInCrm, status, rewardedAt`.
3. In a HubSpot workflow (deal closed won), send the primary contact's email to `/referral-deal-won`.
4. Edit the reward text in **Referral Settings** and **Won Deal Details**, then connect **HubSpot**, **Gmail**, **Slack** and **Google Sheets**.

Every workflow ships inactive with credential placeholders. Connect your own accounts, run one test, then activate.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
    N0["New Referral<br/><small>webhook</small>"]
    N1["Referral Settings<br/><small>set</small>"]
    N2["Normalize Referral<br/><small>set</small>"]
    N3["Valid Referral?<br/><small>if</small>"]
    N4["Confirm Referral<br/><small>respondToWebhook</small>"]
    N5["Find Referrer in HubSpot<br/><small>hubspot</small>"]
    N6["Save Referred Lead<br/><small>hubspot</small>"]
    N7["Referrer in CRM?<br/><small>if</small>"]
    N8["Thank the Referrer<br/><small>gmail</small>"]
    N9["Log Referral<br/><small>googleSheets</small>"]
    N10["Reject Invalid Referral<br/><small>respondToWebhook</small>"]
    N11["Announce Referral<br/><small>slack</small>"]
    N12["Deal Won<br/><small>webhook</small>"]
    N13["Won Deal Details<br/><small>set</small>"]
    N14["Find Open Referral<br/><small>googleSheets</small>"]
    N15["Was a Referral?<br/><small>if</small>"]
    N16["Ask Finance to Send Reward<br/><small>slack</small>"]
    N17["Tell Referrer the Good News<br/><small>gmail</small>"]
    N18["Mark Reward Sent<br/><small>googleSheets</small>"]
    N19["Not a Referral Deal<br/><small>noOp</small>"]
    N20["On Workflow Error<br/><small>errorTrigger</small>"]
    N21["Format Error Details<br/><small>set</small>"]
    N22["Alert #automation-alerts<br/><small>slack</small>"]
    N23["Log to Error Sheet<br/><small>googleSheets</small>"]
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N3 --> N10
    N4 --> N5
    N5 --> N6
    N6 --> N7
    N7 --> N8
    N7 --> N9
    N8 --> N9
    N9 --> N11
    N12 --> N13
    N13 --> N14
    N14 --> N15
    N15 --> N16
    N15 --> N19
    N16 --> N17
    N17 --> N18
    N20 --> N21
    N21 --> N22
    N21 --> N23
```
<!-- ARCHITECTURE:END -->
