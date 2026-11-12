"""Prepare clean SKU-level dataset for the Linda's projected inventory workbook.

Inputs (scratchpad/data):
  ttm_sku.json     ShopifyQL sales by SKU/type/vendor, 2025-11-01..2026-10-31
  ttm_titles.json  ShopifyQL units by SKU/title, same window
  l90_sku.json     ShopifyQL sales by SKU/title, 2026-08-02..2026-10-31 (91 days)
  cat_month.json   ShopifyQL monthly sales by product_type, same TTM window
  inv/*.json       GraphQL productVariants with owned-location inventory levels
  bills/*.json     Bill.com AP bills
Output: data/clean.json
"""
import glob
import json
import re
from collections import defaultdict

D = "/tmp/claude-0/-home-user-AI-Assistance-Ecommerce/9813644c-17c2-5318-9b0b-6a1014819282/scratchpad/data/"
f = lambda x: float(x or 0)

# ----------------------------------------------------------------- categories
CATS = [
    "Batting",
    "Fabric & Pre-Cuts",
    "Cuddle / Minky Fabric",
    "Thread & Bobbins",
    "Interfacing, Stabilizers & Adhesives",
    "Notions, Cutting & Pressing Tools",
    "Patterns, Books & Pantographs",
    "Kits",
    "Machines, Parts & Software",
    "Crafts, Trims & Gifts",
]
NON_INV = "EXCLUDED - Non-inventory"

TYPE_MAP = {
    "Batting": "Batting", "Batting Sample Pack": "Batting",
    "Cuddle Fabric": "Cuddle / Minky Fabric", "Cuddle Kit": "Cuddle / Minky Fabric", "Cuddle Blanket": "Cuddle / Minky Fabric",
    "Interfacing": "Interfacing, Stabilizers & Adhesives", "Woven Interfacing": "Interfacing, Stabilizers & Adhesives",
    "Fusible Stabilizer": "Interfacing, Stabilizers & Adhesives", "Embroidery Stabilzer": "Interfacing, Stabilizers & Adhesives",
    "Non-Woven": "Interfacing, Stabilizers & Adhesives", "Iron-On Vinyl": "Interfacing, Stabilizers & Adhesives",
    "vinyl": "Interfacing, Stabilizers & Adhesives", "Fabric Spray Adhesive": "Interfacing, Stabilizers & Adhesives",
    "Sewable Iron-On Adhesive": "Interfacing, Stabilizers & Adhesives", "No Sew Iron-On Adhesive": "Interfacing, Stabilizers & Adhesives",
    "Quilt Kit": "Kits", "Quilt Kits": "Kits", "Kit": "Kits", "Embroidery Kit": "Kits",
    "Sewing Machine": "Machines, Parts & Software", "Machine Part": "Machines, Parts & Software", "Software": "Machines, Parts & Software",
    "Embroidery Machines": "Machines, Parts & Software", "Sewing & Embroidery Machine": "Machines, Parts & Software",
    "Overlock/Serger": "Machines, Parts & Software", "INNOVA AIO Set": "Machines, Parts & Software",
    "Book": "Patterns, Books & Pantographs", "Designs with Lines": "Patterns, Books & Pantographs",
    "Package Protection": NON_INV, "return,package_protection": NON_INV, "Gift Card": NON_INV,
    "Digital Download": NON_INV, "Free Download": NON_INV, "Download": NON_INV, "DQP": NON_INV, "DQP-RRQ": NON_INV,
}


def categorize(ptype: str, title: str, vendor: str, sku: str) -> str:
    t = (title or "").lower()
    p = ptype or ""
    pl = p.lower()
    # non-inventory first (title-driven so mis-typed items are caught too)
    if any(k in t for k in ("membership", "gift card", "package protection", "shipping protection", "digital download",
                            "digital e2e", "(digital", "e-pattern", "pdf pattern", "gift certificate")):
        return NON_INV
    if p in TYPE_MAP:
        return TYPE_MAP[p]
    if "pantograph" in pl or "pattern" in pl:
        return "Patterns, Books & Pantographs"
    if pl.startswith("thread") or pl.startswith("set - ") or p in ("Threads", "Bobbin", "Machine Embroidery and Quilting Threads"):
        return "Thread & Bobbins"
    if "heatnbond" in pl:
        return "Interfacing, Stabilizers & Adhesives"
    if p in ("Fabric", "Pre-Cuts", "Fat Quarter", "Fat Quarters", "Fat Quarter Bundle", "Panel", "Fabric Panel", "Yardage",
             "3-Yard Pack", '10" Squares', '5" Squares', "Jelly Rolls", "Quilt Backing", "Flannel", "Muslin Fabric",
             "Fleece", "Faux Leather"):
        return "Fabric & Pre-Cuts"
    if p in ("Notion", "Notions", "Notions & Tools", "Sewing", "Quilting", "Magnetic Sewing Pins", "Template", "Zippers",
             "Stencil", "Sew Magnetic Cutting System", "Rulers & Mats", "Ruler", "Scissor", "Needles", "Needle",
             "Topstitch Needles", "Left Handed", "Iron Accessories", "Wool Pressing Mat", "Felt Pressing Mat",
             "Pressing Mat", "Ironing Board", "Ironing Board Cover", "Smart Iron", "Project Iron", "Elastic", "Buttons",
             "Tracing Paper", "Sewing & Quilting Tools", "Art & Crafting Tool Accessories", "Storage & Bags",
             "Carry Bag", "Color Card", "Pillow Form", "EZ Print Sheets") or pl.startswith(("notions", "sewing and quilting")):
        return "Notions, Cutting & Pressing Tools"
    if p in ("Crafts", "Craft", "Gifts", "Needleart", "Embroidery", "Applique", "Cosplay", "Leggings", "T-Shirt", "Tank",
             "Drinkware", "Sticker", "Blanket", "Tie-Back", "Sookie Sews", "Yarn") or any(
            k in pl for k in ("trim", "fringe", "braid", "sequin", "ribbon", "pompom", "cord", "rhinestone", "knitting")):
        return "Crafts, Trims & Gifts"
    # keyword fallback for blank / mixed types (Brewers, product, Physical, '')
    kw = [
        ("Batting", ("batting", "80/20", "warm & natural", "warm and natural", "quilters dream", "wool batt")),
        ("Interfacing, Stabilizers & Adhesives", ("soft & stable", "interfacing", "stabilizer", "fusible", "insul-bright",
                                                   "insul-fleece", "heatnbond", "adhesive", "505 ", "pellon", "decor bond")),
        ("Thread & Bobbins", ("thread", "bobbin", "spool", "isacord", "aurifil")),
        ("Cuddle / Minky Fabric", ("cuddle", "minky")),
        ("Fabric & Pre-Cuts", ("fat quarter", "yard", "fabric", "charm pack", "layer cake", "jelly roll", "bundle", "precut")),
        ("Patterns, Books & Pantographs", ("pattern", "book", "magazine", "pantograph")),
        ("Kits", ("kit", "block of the month", "bom ")),
        ("Machines, Parts & Software", ("machine", "software", "presser foot", " foot", "hoop", "usb", "lightboard", "light board", "embroidery design")),
        ("Notions, Cutting & Pressing Tools", ("blade", "rotary", "shear", "scissor", "snip", "cutting mat", "mat", "ruler",
                                               "pin", "needle", "clip", "tweezer", "iron", "marker", "lubricant", "board",
                                               "tote", "light", "seam ripper", "template", "glue")),
    ]
    for cat, keys in kw:
        if any(k in t for k in keys):
            return cat
    if vendor in ("Famore", "CutterPillar"):
        return "Notions, Cutting & Pressing Tools"
    return "Notions, Cutting & Pressing Tools"  # small residual; flagged as 'category inferred'


# ------------------------------------------------------------------- vendors
VENDOR_LEAD = {  # config/vendors.yaml (days)
    "Hobbs Bonded Fibers": 28, "Quilters Dream Batting": 56, "Pellon": 21, "Warm Company": 21,
    "Checker Distributor": 7, "Brewer Distributor": 7, "Brewer Sewing": 7, "Rnk Distributing": 10, "Shannon Fabrics": 14,
    "Moda Fabrics & Supplies": 14, "Superior Threads": 10, "Famore": 14, "Linda's Electric Quilters": 14,
}
DEFAULT_LEAD = 21
DS_PREFIX = ("QDDS-", "WCDS-", "PDS-")

# ------------------------------------------------------------------ load data
ttm_rows = json.load(open(D + "ttm_sku.json"))["rows"]
l90_rows = json.load(open(D + "l90_sku.json"))["rows"]
titles_rows = json.load(open(D + "ttm_titles.json"))["rows"]

title = {}
for s, pt, vt, u in titles_rows:
    if s and (s not in title or f(u) > title[s][2]):
        title[s] = (pt, vt, f(u))
for s, pt, vt, *_ in l90_rows:
    if s and s not in title:
        title[s] = (pt, vt, 0)

# aggregate TTM by SKU (a SKU can appear under >1 type/vendor if edited mid-year)
sku = {}
unattrib = {"units": 0.0, "gross": 0.0, "net": 0.0, "cogs": 0.0, "rows": 0}
for s, ptype, vendor, units, gross, net, cogs in ttm_rows:
    if not s:
        unattrib["units"] += f(units); unattrib["gross"] += f(gross); unattrib["net"] += f(net); unattrib["cogs"] += f(cogs); unattrib["rows"] += 1
        continue
    r = sku.setdefault(s, {"sku": s, "units": 0.0, "gross": 0.0, "net": 0.0, "cogs": 0.0, "_tv": defaultdict(float)})
    r["units"] += f(units); r["gross"] += f(gross); r["net"] += f(net); r["cogs"] += f(cogs)
    r["_tv"][(ptype, vendor)] += f(net) + 1e-6
for r in sku.values():
    (r["ptype"], r["vendor"]) = max(r["_tv"].items(), key=lambda kv: kv[1])[0]
    del r["_tv"]
    t = title.get(r["sku"], ("", "", 0))
    r["title"], r["variant"] = t[0], ("" if t[1] == "Default Title" else t[1])
    r["l90_units"] = 0.0; r["l90_net"] = 0.0; r["l90_cogs"] = 0.0

l90_unattrib = 0.0
for s, pt, vt, units, net, cogs in l90_rows:
    if not s:
        l90_unattrib += f(net); continue
    if s in sku:
        sku[s]["l90_units"] += f(units); sku[s]["l90_net"] += f(net); sku[s]["l90_cogs"] += f(cogs)

# ------------------------------------------------------- owned inventory (GraphQL)
inv = {}
inv_files = sorted(glob.glob(D + "inv/*.json"))
for fn in inv_files:
    try:
        nodes = json.load(open(fn))["data"]["productVariants"]["nodes"]
    except Exception as e:  # noqa
        print("bad inv file", fn, e); continue
    for n in nodes:
        s = n.get("sku")
        if not s:
            continue
        it = n.get("inventoryItem") or {}
        def q(level, name):
            if not level:
                return 0
            for x in level["quantities"]:
                if x["name"] == name:
                    return x["quantity"]
            return 0
        owned_on_hand = sum(q(it.get(k), "on_hand") for k in ("mck", "ful", "evt", "rtl"))
        owned_avail = q(it.get("mck"), "available") + q(it.get("ful"), "available")
        incoming = q(it.get("mck"), "incoming") + q(it.get("ful"), "incoming")
        committed = q(it.get("mck"), "committed") + q(it.get("ful"), "committed")
        rec = {
            "owned_on_hand": owned_on_hand, "owned_avail": owned_avail, "incoming": incoming, "committed": committed,
            "total_avail": n.get("inventoryQuantity") or 0, "tracked": it.get("tracked", True),
            "unit_cost": f((it.get("unitCost") or {}).get("amount")) or None,
            "price": f(n.get("price")), "policy": n.get("inventoryPolicy"),
            "status": (n.get("product") or {}).get("status"), "title": (n.get("product") or {}).get("title"),
            "vendor": (n.get("product") or {}).get("vendor"), "ptype": (n.get("product") or {}).get("productType"),
            "has_owned_level": any(it.get(k) for k in ("mck", "ful", "evt", "rtl")),
        }
        # same SKU on >1 variant: sum owned stock, keep ACTIVE status if any
        if s in inv:
            o = inv[s]
            for k in ("owned_on_hand", "owned_avail", "incoming", "committed", "total_avail"):
                o[k] += rec[k]
            if rec["status"] == "ACTIVE":
                o["status"] = "ACTIVE"
            o["dup_variants"] = o.get("dup_variants", 1) + 1
            o["unit_cost"] = o["unit_cost"] or rec["unit_cost"]
        else:
            inv[s] = rec

# ------------------------------------------------------------ build SKU rows
out, excluded = [], []
for s, r in sku.items():
    iv = inv.get(s)
    cat = categorize(r["ptype"], r["title"] or (iv or {}).get("title", ""), r["vendor"], s)
    r["category"] = cat
    r["lead"] = VENDOR_LEAD.get(r["vendor"], DEFAULT_LEAD)
    flags = []
    if r["ptype"] in ("", "Brewers", "product", "Physical", "Physcial"):
        flags.append("Category inferred from title")
    # exclusion rules
    reason = None
    if cat == NON_INV:
        reason = "Non-inventory (membership / gift card / protection fee / digital download)"
    elif r["units"] <= 0:
        reason = "Net units <= 0 over TTM (returns exceed sales)"
    elif r["l90_units"] <= 0:
        reason = "No sales in last 91 days - treated as discontinued/inactive"
    elif iv and iv["status"] in ("ARCHIVED",):
        reason = "Product archived in Shopify"
    # unit cost
    avg_cost = r["cogs"] / r["units"] if r["units"] > 0 and r["cogs"] > 0 else None
    if iv and iv["unit_cost"]:
        cost, src = iv["unit_cost"], "Shopify current unit cost"
    elif avg_cost:
        cost, src = avg_cost, "TTM avg COGS / unit"
    else:
        cost, src = None, "Estimated (no cost on file)"
    r["unit_cost"], r["cost_src"] = cost, src
    r["avg_price"] = r["net"] / r["units"] if r["units"] > 0 else 0
    # fulfillment model
    if s.startswith(DS_PREFIX):
        model = "Dropship"
    elif iv is None:
        model = "Not verified"
    elif not iv["tracked"]:
        model = "Dropship"
    elif iv["owned_on_hand"] > 0 or iv["incoming"] > 0:
        ds_feed = iv["total_avail"] - iv["owned_avail"]
        model = "Hybrid" if ds_feed > 0 else "Stocked"
    elif iv["total_avail"] - iv["owned_avail"] > 0:
        model = "Dropship"
    else:
        model = "Stocked"
        flags.append("Stocked SKU currently at zero")
    r["model"] = model
    r["verified"] = "Y" if iv else "N"
    r["status"] = (iv or {}).get("status") or ""
    r["on_hand"] = max(0, (iv or {}).get("owned_on_hand", 0)) if model in ("Stocked", "Hybrid") else 0
    r["incoming"] = max(0, (iv or {}).get("incoming", 0)) if model in ("Stocked", "Hybrid") else 0
    if iv and iv.get("owned_on_hand", 0) < 0:
        flags.append(f"Negative owned on-hand ({iv['owned_on_hand']}) set to 0")
    if iv and iv.get("dup_variants"):
        flags.append(f"SKU shared by {iv['dup_variants']} variants (summed)")
    if iv and iv["status"] in ("DRAFT", "UNLISTED"):
        flags.append(f"Product status {iv['status']}")
    if r["l90_units"] * 365 / 91 > 2 * r["units"] and r["units"] > 0:
        flags.append("Accelerating (L91 run-rate >2x TTM) - not uplifted")
    if cost and r["avg_price"] and cost > r["avg_price"]:
        flags.append("Unit cost exceeds avg net price")
    r["flags"] = "; ".join(flags)
    if reason:
        r["reason"] = reason
        excluded.append(r)
    else:
        out.append(r)

# estimated cost for SKUs without any cost: category TTM COGS/net-sales ratio x avg price
cat_ratio = {}
for c in CATS:
    n = sum(x["net"] for x in out if x["category"] == c and x["cogs"] > 0)
    k = sum(x["cogs"] for x in out if x["category"] == c and x["cogs"] > 0)
    cat_ratio[c] = k / n if n else 0.6
for r in out:
    if r["unit_cost"] is None:
        r["unit_cost"] = r["avg_price"] * cat_ratio[r["category"]]
        r["flags"] = "; ".join(x for x in (r["flags"], f"Cost estimated at category COGS ratio {cat_ratio[r['category']]:.1%}") if x)

# ------------------------------------------------------- monthly phasing by category
cm = json.load(open(D + "cat_month.json"))["rows"]
phase = {c: [0.0] * 12 for c in CATS}
months = sorted({r[0] for r in cm})
for m, ptype, units, net, gross in cm:
    c = categorize(ptype, "", "", "")
    if c in phase:
        phase[c][months.index(m)] += f(net)
for c in CATS:
    tot = sum(phase[c]) or 1
    phase[c] = [x / tot for x in phase[c]]

# ------------------------------------------------------------------ Bill.com
bills = {"ttm": [], "prior": []}
for fn in sorted(glob.glob(D + "bills/*.json")):
    key = "prior" if "prior_" in fn else "ttm"
    try:
        bs = json.load(open(fn))["data"]["bills"]
    except Exception as e:  # noqa
        print("bad bill file", fn, e); continue
    for b in bs:
        bills[key].append({"id": b["id"], "vendor": b["vendorName"], "amount": f(b["amount"]),
                           "created": b["createdTime"][:10], "inv_date": (b.get("invoice") or {}).get("invoiceDate"),
                           "status": b["paymentStatus"], "due": f(b.get("dueAmount"))})
for k in bills:  # de-dup by id
    seen = {}
    for b in bills[k]:
        seen[b["id"]] = b
    bills[k] = list(seen.values())

json.dump({"skus": out, "excluded": excluded, "unattrib": unattrib, "l90_unattrib": l90_unattrib,
           "phase": phase, "months": months, "cats": CATS, "cat_ratio": cat_ratio, "bills": bills,
           "inv_files": len(inv_files), "inv_skus": len(inv)},
          open(D + "clean.json", "w"))

# --------------------------------------------------------------- diagnostics
print("inv files", len(inv_files), "inv skus", len(inv))
print("projected skus", len(out), "excluded", len(excluded))
tot = lambda rs, k: sum(x[k] for x in rs)
print("TTM net: proj %.0f excl %.0f unattrib %.0f sum %.0f" % (tot(out, "net"), tot(excluded, "net"), unattrib["net"],
      tot(out, "net") + tot(excluded, "net") + unattrib["net"]))
print("TTM cogs: proj %.0f excl %.0f unattrib %.0f" % (tot(out, "cogs"), tot(excluded, "cogs"), unattrib["cogs"]))
from collections import Counter
print(Counter(r["model"] for r in out))
print({m: round(sum(r["cogs"] for r in out if r["model"] == m)) for m in ("Stocked", "Hybrid", "Dropship", "Not verified")})
print("owned on hand @cost", round(sum(r["on_hand"] * r["unit_cost"] for r in out)), "incoming @cost", round(sum(r["incoming"] * r["unit_cost"] for r in out)))
print(Counter(r["reason"] for r in excluded))
print({c: round(sum(r["net"] for r in out if r["category"] == c)) for c in CATS})
print("bills", {k: (len(v), round(sum(b["amount"] for b in v))) for k, v in bills.items()})
