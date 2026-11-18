"""Build assets/portfolio-hero.png, the README banner.

Collages six canvas.png screenshots from this repo with the outcome each
workflow produced in production (same figures as the README impact table).

    pip install pillow
    python scripts/build_hero.py

Uses the macOS system font; pass a .ttf path as the second argument elsewhere.
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
repo = Path(__file__).resolve().parent.parent; out = repo / "assets" / "portfolio-hero.png"
TILES = [
 ("abandoned_cart_recovery_engine", "Abandoned Cart Recovery", "14% of carts recovered · +9% revenue"),
 ("woocommerce_ai_support_agent", "WooCommerce AI Support Agent", "68% of tickets resolved without a human"),
 ("automated_invoice_document_processing", "Automated Invoice Processing", "Month-end close: 3 days → near zero"),
 ("cv_processing_workflow", "AI Applicant Screening", "200+ CVs per opening · −80% screening time"),
 ("order_fulfillment_sync_automation", "Order & Fulfillment Sync", "1,500+ orders/mo · −95% entry errors"),
 ("ai_review_reputation_manager", "AI Review & Reputation Manager", "Rating 4.2 → 4.7★ in 6 months"),
]
BG=(13,17,23); CARD=(22,27,34); BORDER=(48,54,61); FG=(230,237,243); MUTED=(139,148,158); ACCENT=(234,75,113)
W, COLS, PAD, GAP = 2000, 3, 64, 28
TW = (W - 2*PAD - (COLS-1)*GAP)//COLS; IH = int(TW*0.56); LH = 104; TH = IH+LH
SF = sys.argv[1] if len(sys.argv) > 1 else "/System/Library/Fonts/SFNS.ttf"
def f(sz, wt=None):
    ft=ImageFont.truetype(SF, sz)
    if wt:
        try: ft.set_variation_by_name(wt)
        except Exception: pass
    return ft
title=f(50,"Bold"); sub=f(26); name=f(25,"Semibold"); outc=f(21)
HEAD=214; rows=(len(TILES)+COLS-1)//COLS
H = HEAD + rows*TH + (rows-1)*GAP + PAD
img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
d.text((PAD,PAD-6),"81 production-style n8n workflows",font=title,fill=FG)
d.text((PAD,PAD+62),"Real canvases from this repo · outcomes from live client deployments",font=sub,fill=MUTED)
d.rectangle((PAD,PAD+112,PAD+96,PAD+117),fill=ACCENT)
for i,(folder,label,result) in enumerate(TILES):
    x=PAD+(i%COLS)*(TW+GAP); y=HEAD+(i//COLS)*(TH+GAP)
    m=Image.new("L",(TW,TH),0); ImageDraw.Draw(m).rounded_rectangle((0,0,TW-1,TH-1),18,fill=255)
    card=Image.new("RGB",(TW,TH),CARD)
    shot=Image.open(f"{repo}/{folder}/canvas.png").convert("RGB")
    shot=ImageOps.pad(shot,(TW,IH),color=shot.getpixel((2,2)),centering=(0.5,0.5))
    card.paste(shot,(0,0)); cd=ImageDraw.Draw(card)
    cd.line((0,IH,TW,IH),fill=BORDER,width=2)
    cd.text((24,IH+20),label,font=name,fill=FG); cd.text((24,IH+58),result,font=outc,fill=MUTED)
    img.paste(card,(x,y),m)
    ImageDraw.Draw(img).rounded_rectangle((x,y,x+TW-1,y+TH-1),18,outline=BORDER,width=2)
img.save(out,optimize=True); print(out, img.size)
