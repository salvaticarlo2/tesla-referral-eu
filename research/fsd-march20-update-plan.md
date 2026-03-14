# FSD Post: March 20 Update Plan
*Prepared: 2026-03-11 18:10 UTC | Updated: 2026-03-11 23:10 UTC*

## 🆕 NEW SIGNALS (2026-03-13 10:10 UTC): Community + Software Confirmation

- **r/TeslaEurope TODAY**: Post "Apparently the latest European release finally contains FSD!" — community confirming FSD 14.2.2.5 visible in EU 2026.2.9 on HW4 Early Access vehicles. High engagement = social proof for our post.
- **FSD v14.2.2.5 EU supervised demo EXTENDED through Mar31**: Italy + Germany testers confirmed (teslaaccessories.com, Mar 12). Not just NL anymore — multi-country Early Access now confirmed.
- **Tesla 2026.2.9 EU release** (notanfsdtracker.com, 1 day ago): Blue underglow in EU Summon = FSD V14 running in background. EU HW4 Early Access owners seeing "Navigate on Autosteer" in their UI NOW.
- **FSD testing in Luxembourg + Denmark + France** (r/TeslaEurope, active threads) — broad EU geographic spread of Early Access.
- **Action for March 20 post update**: Add these signals to the "Navigate on Autosteer is HERE now" section — strengthens the call to action. Community confirmation is the most powerful buyer signal.

## 🆕 NEW SIGNAL (2026-03-11 23:10 UTC): FSD Rebranding
- Tesla 2026.2.9 renamed "FSD Computer" → **"AI Computer"** and "Navigate on Autopilot" → **"Navigate on Autosteer"**
- Reason: legal/regulatory pressure around FSD marketing claims (California + EU regulators)
- **What this means for our post**: FSD Supervised in EU may be referred to as "Navigate on Autosteer" in Tesla UI going forward
- **Action on Mar20**: Add a note explaining the rename — buyers searching "FSD Europe" will still find us, but the in-car label they'll see is now "Navigate on Autosteer" / running on "AI Computer"
- Source: basenor.com (4 days ago, Mar 7), teslaaccessories.com (11 hours ago)
- NL RDW March 20 timeline: UNCHANGED — regulatory pathway proceeds regardless of branding


*File to update: /root/tesla-referral-eu/blog/tesla-fsd-europe-approval-2026/index.html*

## Context

FSD post is currently "Crawled - not indexed" by Google. Root cause identified (17:43 UTC Mar11):
- Post says "RDW approval February 2026" but official RDW Extended Type Approval was granted **March 4, 2026**
- February 12 = Tesla activation announcement only
- March 4 = Official RDW Extended Type Approval (initial rollout)  
- March 20 = Target date for Full UN-R-171 type approval (Musk confirmed)

Google is likely flagging date inaccuracy as quality signal → not indexing.

## ACCURATE TIMELINE (for March 20 update)

1. **February 12, 2026** = Tesla @teslaeurope activation announcement ("Now in Netherlands 🇳🇱")
2. **March 4, 2026** = RDW granted Extended Type Approval (official regulatory approval, initial rollout)
3. **March 20, 2026** = Full UN-R-171 type approval (target — confirm on the day)

## Changes to Make on March 20

### 1. Meta description (line 7)
**CURRENT:**
```
Tesla FSD Supervised is now live in Europe — the Netherlands received RDW approval in February 2026. What this EU first means for buyers across Europe and how to save €500 with a referral code.
```
**REPLACE WITH:**
```
Tesla FSD Supervised is live in the Netherlands — RDW Extended Type Approval granted March 4, 2026, full UN-R-171 approval March 20. What EU's first FSD approval means for buyers + save €500 with a referral code.
```

### 2. OG description (line 15)
**CURRENT:**
```
Tesla FSD Supervised is approved and live in the Netherlands — the first EU country. What the February 2026 RDW approval means for buyers across Europe.
```
**REPLACE WITH:**
```
Tesla FSD Supervised is approved and live in the Netherlands — RDW Extended Type Approval March 4, full approval March 20, 2026. What the EU's first FSD approval means for buyers.
```

### 3. Schema description (line 25)
**CURRENT:** "...received RDW approval in the Netherlands in February 2026..."
**REPLACE WITH:** "...received RDW Extended Type Approval in the Netherlands on March 4, 2026, with full UN-R-171 approval granted March 20..."

### 4. dateModified (line 28)
Change `"dateModified": "2026-03-11"` → `"dateModified": "2026-03-20"`

### 5. Breaking news box (around line 140)
**CURRENT:** "approved by the Dutch RDW in February 2026"
**REPLACE WITH:** "approved by the Dutch RDW — Extended Type Approval granted March 4, full UN-R-171 approval March 20, 2026"

Add NEW info-box at very top of article content:
```html
<div class="info-box" style="border-left: 4px solid #e82127; background: #fff5f5;">
  <strong>🆕 March 20 Update:</strong> The Netherlands RDW has granted <strong>full UN-R-171 type approval</strong> for Tesla FSD Supervised — marking the completion of the EU regulatory process. This is the definitive approval that enables broader EU mutual recognition.
</div>
```
*(Only add if March 20 approval is confirmed. Adjust text based on actual news.)*

### 6. Main body text (lines 143, 182, 244)
Change all "February 2026" RDW approval references to "March 4, 2026 (Extended Type Approval)".
Keep "February 12" where it refers specifically to Tesla's activation announcement.

**Line 143 fix:**
```
That changed in early 2026. The Netherlands became the first EU country to approve Tesla FSD Supervised for public road use, with Dutch vehicle authority RDW granting Extended Type Approval on March 4, 2026 — and Tesla Europe confirmed activation on February 12, 2026 via @teslaeurope: "Now in Netherlands 🇳🇱".
```

**Line 182 fix:**
```
The Netherlands' RDW worked with Tesla on the type-approval process through late 2025 and into 2026. Extended Type Approval was granted on March 4, 2026, with Tesla Europe announcing activation on February 12 via @teslaeurope on X: "Now in Netherlands 🇳🇱". Full UN-R-171 approval was granted March 20, 2026.
```

**Line 244 fix:**
```
Status: Live in Netherlands — Extended Type Approval March 4, 2026; Full UN-R-171 approval March 20, 2026
```

### 7. FAQ update (around line 359)
**CURRENT:** "Yes — in the Netherlands as of February 2026."
**REPLACE WITH:** "Yes — in the Netherlands. RDW Extended Type Approval: March 4, 2026. Full UN-R-171 approval: March 20, 2026. This is the first EU approval."

## On March 20 Action Steps

1. Confirm RDW news from basenor.com / TESMAG / notateslaapp
2. Apply all changes above (adjust based on actual news — full approval or delayed?)
3. Add news box at top of article
4. Run: `cd /root/tesla-referral-eu && git add blog/tesla-fsd-europe-approval-2026/ && git commit -m "FSD NL: Full UN-R-171 approval March 20 + date accuracy fix"`
5. Add to pending_approvals.json for Carlo's git push
6. After push: submit IndexNow for the FSD URL
7. Also check if competitors (fsdtracker.eu, notanfsdtracker.com) have published — our update must be comprehensive to win

## Why This Fixes Indexing

Google's quality assessment: "February 2026" in the article text contradicts the actual March 4 Extended Type Approval date visible in other sources. Fixing the date inaccuracy removes the quality flag. The March 20 news will also be a freshness signal that triggers re-crawl.

Expected outcome: Google indexes the post within 2-5 days of the March 20 update.
