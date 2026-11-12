"""Build the bank-ready projected inventory workbook from data/clean.json."""
import json
from datetime import date

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL
from openpyxl.worksheet.table import Table, TableStyleInfo

S = "/tmp/claude-0/-home-user-AI-Assistance-Ecommerce/9813644c-17c2-5318-9b0b-6a1014819282/scratchpad/"
OUT = "/home/user/AI-Assistance-Ecommerce/reports/Lindas_Projected_Inventory_Nov2026-Oct2027.xlsx"
d = json.load(open(S + "data/clean.json"))
CATS = d["cats"]
skus, excl, un = d["skus"], d["excluded"], d["unattrib"]

# ---------------------------------------------------------------- control totals
# Source: ShopifyQL `FROM sales SHOW net_sales, cost_of_goods_sold, net_items_sold TIMESERIES month
#         SINCE 2025-11-01 UNTIL 2026-10-31`, pulled 2026-11-12.
CTRL_MONTHS = [("Nov-25", 1121760.23, 658580.01, 53426), ("Dec-25", 768144.29, 459798.85, 39833),
               ("Jan-26", 981090.98, 595739.22, 51560), ("Feb-26", 1083676.97, 712552.50, 58253),
               ("Mar-26", 1330654.83, 851635.99, 63246), ("Apr-26", 1292892.50, 856322.70, 63963),
               ("May-26", 1540077.18, 1043976.98, 77220), ("Jun-26", 1386436.08, 955837.00, 73183),
               ("Jul-26", 1226689.57, 801188.23, 66843), ("Aug-26", 953308.68, 562995.80, 48112),
               ("Sep-26", 1308209.55, 715940.54, 54339), ("Oct-26", 1202317.64, 714430.32, 51625)]
PRIOR_TTM_NET = 9640000  # placeholder replaced below
PRIOR_MONTHS = [807401.41, 535637.58, 535969.99, 697564.34, 833634.73, 846245.17, 1036645.98, 799953.36,
                811558.49, 858939.00, 939311.94, 937336.14]  # Nov-24..Oct-25 net sales, same ShopifyQL source
PRIOR_TTM_NET = sum(PRIOR_MONTHS)
L91_CTRL = 3432349.60  # ShopifyQL sales by SKU 2026-08-02..2026-10-31, sum of net_sales
SHOPIFY_INV_VALUE_ALL = 10034159582  # ShopifyQL inventory ending_inventory_value all locations, 2026-11-12
SHOPIFY_INV_UNITS_ALL = 1349935434
MTD = (387880.28, 322207.19)  # Nov 1-11 2026 vs Nov 1-11 2025 net sales

# ---------------------------------------------------------------- styles
AR = "Arial"
F = lambda **k: Font(name=AR, size=k.pop("size", 10), **k)
BLUE, GREEN = "0000FF", "008000"
HDR_FILL = PatternFill("solid", fgColor="1F3864")
SUB_FILL = PatternFill("solid", fgColor="D9E1F2")
INPUT_FILL = PatternFill("solid", fgColor="FFFF00")
TOT_FILL = PatternFill("solid", fgColor="F2F2F2")
thin = Side(style="thin", color="BFBFBF")
BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
TOP2 = Border(top=Side(style="thin", color="000000"), bottom=Side(style="double", color="000000"))
USD = '$#,##0;($#,##0);"-"'
USD2 = '$#,##0.00;($#,##0.00);"-"'
NUM = '#,##0;(#,##0);"-"'
NUM1 = '#,##0.0;(#,##0.0);"-"'
PCT = '0.0%;(0.0%);"-"'
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

wb = Workbook()


def header_row(ws, row, labels, widths=None, height=42):
    for i, lab in enumerate(labels, 1):
        c = ws.cell(row=row, column=i, value=lab)
        c.font = F(bold=True, color="FFFFFF")
        c.fill = HDR_FILL
        c.alignment = CENTER
        c.border = BOX
        if widths:
            ws.column_dimensions[CL(i)].width = widths[i - 1]
    ws.row_dimensions[row].height = height


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = F(bold=True, size=14, color="1F3864")
    if sub:
        ws["A2"] = sub
        ws["A2"].font = F(italic=True, size=9, color="595959")
    ws.sheet_view.showGridLines = False


# ====================================================================== Assumptions
A = wb.active
A.title = "Assumptions"
title(A, "Assumptions & Inputs", "Yellow cells with blue text are inputs - change them and every sheet recalculates. "
      "Blue text = hard-coded source data; black = formulas; green = links to other sheets.")
A.column_dimensions["A"].width = 46
A.column_dimensions["B"].width = 16
A.column_dimensions["C"].width = 90
inputs = [
    ("Projection period start", date(2026, 11, 1), "mm/dd/yyyy", "First month of the 12-month projection."),
    ("Projection period end", date(2027, 10, 31), "mm/dd/yyyy", "Last day of the 12-month projection."),
    ("Base-case demand growth vs. trailing 12 months", 0.10, PCT,
     f"Bank base case. Observed: TTM net sales +{(sum(m[1] for m in CTRL_MONTHS)/PRIOR_TTM_NET-1):.0%} YoY; "
     f"Aug-Oct 2026 +{((953308.68+1308209.55+1202317.64)/(858939.00+939311.94+937336.14)-1):.0%} YoY; "
     f"Nov 1-11 2026 +{MTD[0]/MTD[1]-1:.0%} YoY. Base case is deliberately set below half the observed trend."),
    ("Downside sensitivity growth", 0.00, PCT, "Flat demand: projection equals trailing-12-month units."),
    ("Upside sensitivity growth", 0.20, PCT, "Still below the trailing quarter's observed growth."),
    ("Target cover days - Stocked SKUs", 45, NUM,
     "Owned stock held at Linda's locations at period end, in days of forward demand. Source: config/agent.yaml "
     "purchasing.target_cover_days = 45 (vendor lead times 7-56 days + 7-day review period + safety stock)."),
    ("Target cover days - Hybrid SKUs", 21, NUM,
     "SKUs Linda's stocks AND the vendor also drop-ships (e.g., Hobbs rolls). Lower cover because the vendor "
     "warehouse absorbs part of demand."),
    ("Declining-SKU test (L91 run-rate as % of TTM)", 0.50, PCT,
     "If a SKU's last-91-day annualized units fall below this share of its TTM units, demand is based on the "
     "lower L91 run-rate instead of TTM (conservative). Accelerating SKUs are NOT uplifted."),
    ("Recent window length (days)", 91, NUM, "Aug 2 - Oct 31, 2026."),
    ("Days per year", 365, NUM, "Annualization factor."),
    ("Assortment rotation haircut", 0.75, PCT,
     "Applied to the measured replacement ratio below. Retired SKUs (no sales in last 91 days) are not projected "
     "individually; new SKUs that replace them are provided for at category level at this haircut."),
]
r0 = 4
for i, (lab, val, fmt, note) in enumerate(inputs):
    r = r0 + i
    A.cell(row=r, column=1, value=lab).font = F(bold=True)
    c = A.cell(row=r, column=2, value=val)
    c.font = F(color=BLUE)
    c.fill = INPUT_FILL
    c.number_format = fmt
    c.border = BOX
    A.cell(row=r, column=3, value=note).font = F(size=9)
    A.cell(row=r, column=3).alignment = WRAP
    A.row_dimensions[r].height = 30
NAMES = {"start": "$B$4", "end": "$B$5", "g": "$B$6", "gL": "$B$7", "gH": "$B$8", "cs": "$B$9", "ch": "$B$10",
         "thr": "$B$11", "win": "$B$12", "yr": "$B$13", "hc": "$B$14"}
AS = {k: f"Assumptions!{v}" for k, v in NAMES.items()}

# monthly phasing
pr = r0 + len(inputs) + 2
A.cell(row=pr, column=1, value="Monthly demand phasing by category (share of TTM net sales by calendar month)").font = F(bold=True, size=11, color="1F3864")
A.cell(row=pr + 1, column=1, value="Source: ShopifyQL net sales by product_type, Nov-2025 to Oct-2026, mapped to categories. "
       "Projection month N uses the same calendar month's share last year (embeds seasonality).").font = F(italic=True, size=9)
mon_labels = ["Nov-26", "Dec-26", "Jan-27", "Feb-27", "Mar-27", "Apr-27", "May-27", "Jun-27", "Jul-27", "Aug-27", "Sep-27", "Oct-27"]
hr = pr + 2
A.cell(row=hr, column=1, value="Category").font = F(bold=True)
for j, m in enumerate(mon_labels):
    c = A.cell(row=hr, column=2 + j, value=m)
    c.font = F(bold=True); c.alignment = CENTER; c.fill = SUB_FILL
    A.column_dimensions[CL(2 + j)].width = max(A.column_dimensions[CL(2 + j)].width or 0, 11)
A.cell(row=hr, column=14, value="Total").font = F(bold=True)
PHASE_ROW = {}
tot_net = [sum(m[1] for m in CTRL_MONTHS)]
company_phase = [m[1] / tot_net[0] for m in CTRL_MONTHS]
for i, cat in enumerate(CATS + ["Company total (used for unattributed sales)"]):
    r = hr + 1 + i
    PHASE_ROW[cat] = r
    A.cell(row=r, column=1, value=cat)
    vals = d["phase"][cat] if cat in d["phase"] else company_phase
    for j, v in enumerate(vals):
        if j == 11:
            c = A.cell(row=r, column=2 + j, value=f"=1-SUM(B{r}:L{r})")
            c.comment = Comment("Balancing share so each row sums to exactly 100%.", "Model")
        else:
            c = A.cell(row=r, column=2 + j, value=round(v, 6)); c.font = F(color=BLUE)
        c.number_format = PCT
    c = A.cell(row=r, column=14, value=f"=SUM(B{r}:M{r})")
    c.number_format = PCT
PHASE_ROW["Unattributed"] = PHASE_ROW["Company total (used for unattributed sales)"]

# rotation evidence
er = hr + len(CATS) + 4
A.cell(row=er, column=1, value="Assortment rotation evidence (measured)").font = F(bold=True, size=11, color="1F3864")
A.cell(row=er + 1, column=1, value="Retired = SKUs with TTM sales but none in the last 91 days. New = SKUs whose last-91-day units are >=90% "
       "of TTM units (launched in the last quarter), annualized. Ratio = MIN(1, New / Retired).").font = F(italic=True, size=9)
labs = ["Category", "Retired SKUs TTM net sales $", "New SKUs annualized net sales $", "Replacement ratio (capped 100%)", "Allowance factor (ratio x haircut)"]
for j, lab in enumerate(labs):
    c = A.cell(row=er + 2, column=1 + j, value=lab)
    c.font = F(bold=True); c.fill = SUB_FILL; c.alignment = CENTER
A.row_dimensions[er + 2].height = 30
ROT_ROW = {}
for i, cat in enumerate(CATS):
    r = er + 3 + i
    ROT_ROW[cat] = r
    ret = sum(x["net"] for x in excl if x["category"] == cat and x["reason"].startswith("No sales"))
    new = sum(x["l90_net"] for x in skus if x["category"] == cat and x["l90_units"] >= 0.9 * x["units"]) * 365 / 91
    A.cell(row=r, column=1, value=cat)
    A.cell(row=r, column=2, value=round(ret, 2)).font = F(color=BLUE)
    A.cell(row=r, column=3, value=round(new, 2)).font = F(color=BLUE)
    A.cell(row=r, column=4, value=f"=IF(B{r}=0,0,MIN(1,C{r}/B{r}))")
    A.cell(row=r, column=5, value=f"=D{r}*{NAMES['hc']}")
    for col, fmt in ((2, USD), (3, USD), (4, PCT), (5, PCT)):
        A.cell(row=r, column=col).number_format = fmt

# ====================================================================== SKU Detail
W = wb.create_sheet("SKU Detail")
title(W, "SKU Detail - Projected 12-Month Inventory Requirement (Nov 2026 - Oct 2027)",
      "One row per active SKU. Source data in blue (Shopify sales/inventory as of 2026-11-12); projections are live formulas "
      "driven by the Assumptions sheet. Sorted by base-case new purchases $.")
cols = [
    ("Rank", 6), ("SKU", 18), ("Product Title", 44), ("Variant", 16), ("Vendor", 22), ("Shopify Product Type", 16),
    ("Category", 24), ("Fulfillment Model", 12), ("Owned Inventory Verified", 10), ("Shopify Status", 10),
    ("Vendor Lead Time (days)", 9), ("TTM Units", 10), ("TTM Net Sales $", 13), ("TTM COGS $", 13), ("L91 Units", 9),
    ("Unit Cost $", 10), ("Cost Source", 16), ("Avg Net Price $", 10), ("Demand Basis", 13), ("Base Annual Units", 11),
    ("Proj 12M Units", 11), ("Proj 12M Net Sales $", 13), ("Proj 12M COGS $", 13), ("Owned On-Hand Units", 10),
    ("Owned On-Hand $ (cost)", 12), ("Open PO / Incoming Units", 10), ("Open PO $ (cost)", 11),
    ("Target Ending Units", 10), ("Target Ending $ (cost)", 12), ("New Purchase Units", 11), ("New Purchase $ (cost)", 13),
    ("Excess Units (beyond 12M need)", 11), ("Excess $ (cost)", 11), ("Current Days of Cover", 9),
    ("New Purchase $ @ Downside", 13), ("New Purchase $ @ Upside", 13), ("Data Flags", 50),
]
HR = 4
header_row(W, HR, [c[0] for c in cols], [c[1] for c in cols], height=54)
W.freeze_panes = W.cell(row=HR + 1, column=4)


def rank_key(x):
    u = x["units"]; l = x["l90_units"] * 365 / 91
    base = l if l < 0.5 * u else u
    proj = base * 1.10
    cover = 45 if x["model"] == "Stocked" else (21 if x["model"] == "Hybrid" else 0)
    return -max(0, proj + proj / 365 * cover - x["on_hand"] - x["incoming"]) * (x["unit_cost"] or 0)


skus.sort(key=rank_key)
first = HR + 1
last = first + len(skus) - 1
g, gL, gH, cs, ch, thr, win, yr = (AS[k] for k in ("g", "gL", "gH", "cs", "ch", "thr", "win", "yr"))
for i, x in enumerate(skus):
    r = first + i
    vals = [i + 1, x["sku"], x["title"], x["variant"], x["vendor"], x["ptype"], x["category"], x["model"], x["verified"],
            x["status"], x["lead"], round(x["units"]), round(x["net"], 2), round(x["cogs"], 2), round(x["l90_units"]),
            round(x["unit_cost"], 4), x["cost_src"]]
    for j, v in enumerate(vals, 1):
        c = W.cell(row=r, column=j, value=v)
        if j >= 11:
            c.font = F(color=BLUE)
    R = str(r)
    W.cell(row=r, column=18, value=f"=IFERROR(M{R}/L{R},0)")
    W.cell(row=r, column=19, value=f'=IF(O{R}*{yr}/{win}<L{R}*{thr},"L91 run-rate (declining)","TTM")')
    W.cell(row=r, column=20, value=f"=IF(O{R}*{yr}/{win}<L{R}*{thr},O{R}*{yr}/{win},L{R})")
    W.cell(row=r, column=21, value=f"=T{R}*(1+{g})")
    W.cell(row=r, column=22, value=f"=U{R}*R{R}")
    W.cell(row=r, column=23, value=f"=U{R}*P{R}")
    W.cell(row=r, column=24, value=x["on_hand"]).font = F(color=BLUE)
    W.cell(row=r, column=25, value=f"=X{R}*P{R}")
    W.cell(row=r, column=26, value=x["incoming"]).font = F(color=BLUE)
    W.cell(row=r, column=27, value=f"=Z{R}*P{R}")
    cov = f'IF(H{R}="Stocked",{cs},IF(H{R}="Hybrid",{ch},0))'
    W.cell(row=r, column=28, value=f"=U{R}/{yr}*{cov}")
    W.cell(row=r, column=29, value=f"=AB{R}*P{R}")
    W.cell(row=r, column=30, value=f"=MAX(0,U{R}+AB{R}-X{R}-Z{R})")
    W.cell(row=r, column=31, value=f"=AD{R}*P{R}")
    W.cell(row=r, column=32, value=f"=MAX(0,X{R}+Z{R}-U{R}-AB{R})")
    W.cell(row=r, column=33, value=f"=AF{R}*P{R}")
    W.cell(row=r, column=34, value=f"=IF(U{R}>0,X{R}/(U{R}/{yr}),0)")
    W.cell(row=r, column=35, value=f"=MAX(0,T{R}*(1+{gL})*(1+{cov}/{yr})-X{R}-Z{R})*P{R}")
    W.cell(row=r, column=36, value=f"=MAX(0,T{R}*(1+{gH})*(1+{cov}/{yr})-X{R}-Z{R})*P{R}")
    W.cell(row=r, column=37, value=x["flags"])
fmts = {12: NUM, 13: USD, 14: USD, 15: NUM, 16: USD2, 18: USD2, 20: NUM1, 21: NUM1, 22: USD, 23: USD, 24: NUM, 25: USD,
        26: NUM, 27: USD, 28: NUM1, 29: USD, 30: NUM1, 31: USD, 32: NUM1, 33: USD, 34: NUM, 35: USD, 36: USD}
for col, fmt in fmts.items():
    for r in range(first, last + 1):
        W.cell(row=r, column=col).number_format = fmt
# totals row above header
W.cell(row=3, column=11, value="Totals:").font = F(bold=True)
for col in (12, 13, 14, 15, 22, 23, 25, 27, 29, 31, 33, 35, 36):
    c = W.cell(row=3, column=col, value=f"=SUBTOTAL(9,{CL(col)}{first}:{CL(col)}{last})")
    c.font = F(bold=True); c.number_format = fmts[col]; c.fill = TOT_FILL
tab = Table(displayName="SKUDetail", ref=f"A{HR}:{CL(len(cols))}{last}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
W.add_table(tab)
W.cell(row=HR, column=24).comment = Comment("Units on hand at Linda's own locations only (McKinney TX, Springfield TN "
                                            "fulfillment center, event & retail popups). Vendor drop-ship feed quantities "
                                            "are excluded. Populated only where Owned Inventory Verified = Y.", "Model")
W.cell(row=HR, column=8).comment = Comment("Stocked: Linda's holds the inventory. Hybrid: Linda's holds stock AND the vendor "
                                           "drop-ships. Dropship: vendor ships direct, no owned stock (purchase = demand). "
                                           "Not verified: tail SKU not checked by location; modeled order-to-demand "
                                           "(no stock build, no on-hand credit).", "Model")
SK = "'SKU Detail'!"
rng = lambda col: f"{SK}${col}${first}:${col}${last}"

# ====================================================================== Exclusions
X = wb.create_sheet("Exclusions")
title(X, "Exclusions - TTM sales not projected at SKU level",
      "Every SKU with TTM activity that is not in SKU Detail, with the reason. Retired-SKU volume is replaced at "
      "category level via the assortment rotation allowance (see Assumptions).")
xcols = [("SKU", 20), ("Product Title", 50), ("Vendor", 22), ("Shopify Product Type", 18), ("Category", 26),
         ("Exclusion Reason", 48), ("TTM Units", 10), ("TTM Net Sales $", 13), ("TTM COGS $", 13), ("L91 Units", 9)]
header_row(X, 4, [c[0] for c in xcols], [c[1] for c in xcols])
excl.sort(key=lambda x: (x["reason"], -x["net"]))
xf = 5
rows_x = [(x["sku"], x["title"], x["vendor"], x["ptype"], x["category"], x["reason"], round(x["units"]), round(x["net"], 2),
           round(x["cogs"], 2), round(x["l90_units"])) for x in excl]
rows_x.append(("(no SKU)", "Line items with no SKU / deleted products / custom POS items (" + str(un["rows"]) + " source rows)",
               "Various", "", "Unattributed", "No SKU - projected at company level (order-to-demand)",
               round(un["units"]), round(un["net"], 2), round(un["cogs"], 2), 0))
for i, row in enumerate(rows_x):
    for j, v in enumerate(row, 1):
        c = X.cell(row=xf + i, column=j, value=v)
        if j >= 7:
            c.font = F(color=BLUE)
            c.number_format = USD if j in (8, 9) else NUM
xl = xf + len(rows_x) - 1
X.cell(row=3, column=6, value="Totals:").font = F(bold=True)
for col in (7, 8, 9):
    c = X.cell(row=3, column=col, value=f"=SUBTOTAL(9,{CL(col)}{xf}:{CL(col)}{xl})")
    c.font = F(bold=True); c.number_format = USD if col > 7 else NUM; c.fill = TOT_FILL
t2 = Table(displayName="Exclusions", ref=f"A4:J{xl}")
t2.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
X.add_table(t2)
X.freeze_panes = "B5"
XR = lambda col: f"Exclusions!${col}${xf}:${col}${xl}"
RET = "No sales in last 91 days - treated as discontinued/inactive"

# ====================================================================== Category Summary
C = wb.create_sheet("Category Summary", 0)
title(C, "Projected Inventory Purchases by Product Category - 12 Months Nov 2026 to Oct 2027",
      "All figures at cost unless labelled net sales. Every value is a formula over SKU Detail / Exclusions / Assumptions.")
C["A3"] = "Base-case growth:"
C["A3"].font = F(bold=True)
C["B3"] = f"={AS['g']}"
C["B3"].font = F(color=GREEN); C["B3"].number_format = PCT
ccols = [("Product Category", 34), ("Active SKUs", 9), ("TTM Units (active SKUs)", 11), ("TTM Net Sales $ (active SKUs)", 14),
         ("TTM COGS $ (active SKUs)", 13), ("TTM Net Sales $ (retired SKUs)", 13), ("TTM COGS $ (retired SKUs)", 12),
         ("TTM Gross Margin %", 9), ("Owned On-Hand $ (cost)", 12), ("Open POs $ (cost)", 11),
         ("Proj 12M Units (active SKUs)", 12), ("Proj 12M Net Sales $ (active SKUs)", 14), ("Proj 12M COGS $ (active SKUs)", 13),
         ("Assortment Rotation Allowance $", 12), ("Total Proj 12M COGS $", 14), ("Target Ending Inventory $", 12),
         ("Excess Inventory $ (beyond 12M need)", 12), ("New Purchases $ - Base Case", 14),
         ("of which Stocked / Hybrid $", 13), ("of which Dropship / Order-to-Demand $", 13),
         ("Total Purchase Requirement $ (Open POs + New)", 15), ("% of Total", 8), ("Projected Inventory Turns", 9),
         ("New Purchases $ - Downside", 13), ("New Purchases $ - Upside", 13),
         ("Rotation Allowance - Net Sales $", 13), ("Total Proj 12M Net Sales $", 14)]
CH = 5
header_row(C, CH, [c[0] for c in ccols], [c[1] for c in ccols], height=66)
CAT_ROW = {}
cr = CH + 1
for i, cat in enumerate(CATS):
    r = cr + i
    CAT_ROW[cat] = r
    R = str(r)
    q = f'{rng("G")},$A{R}'
    C.cell(row=r, column=1, value=cat).font = F(bold=True)
    C.cell(row=r, column=2, value=f"=COUNTIFS({q})")
    C.cell(row=r, column=3, value=f"=SUMIFS({rng('L')},{q})")
    C.cell(row=r, column=4, value=f"=SUMIFS({rng('M')},{q})")
    C.cell(row=r, column=5, value=f"=SUMIFS({rng('N')},{q})")
    C.cell(row=r, column=6, value=f'=SUMIFS({XR("H")},{XR("E")},$A{R},{XR("F")},"{RET}")')
    C.cell(row=r, column=7, value=f'=SUMIFS({XR("I")},{XR("E")},$A{R},{XR("F")},"{RET}")')
    C.cell(row=r, column=8, value=f"=IFERROR(1-(E{R}+G{R})/(D{R}+F{R}),0)")
    C.cell(row=r, column=9, value=f"=SUMIFS({rng('Y')},{q})")
    C.cell(row=r, column=10, value=f"=SUMIFS({rng('AA')},{q})")
    C.cell(row=r, column=11, value=f"=SUMIFS({rng('U')},{q})")
    C.cell(row=r, column=12, value=f"=SUMIFS({rng('V')},{q})")
    C.cell(row=r, column=13, value=f"=SUMIFS({rng('W')},{q})")
    C.cell(row=r, column=14, value=f"=G{R}*Assumptions!$E${ROT_ROW[cat]}*(1+{g})")
    C.cell(row=r, column=15, value=f"=M{R}+N{R}")
    C.cell(row=r, column=16, value=f"=SUMIFS({rng('AC')},{q})")
    C.cell(row=r, column=17, value=f"=SUMIFS({rng('AG')},{q})")
    C.cell(row=r, column=18, value=f"=SUMIFS({rng('AE')},{q})+N{R}")
    C.cell(row=r, column=19, value=f'=SUMIFS({rng("AE")},{q},{rng("H")},"Stocked")+SUMIFS({rng("AE")},{q},{rng("H")},"Hybrid")')
    C.cell(row=r, column=20, value=f"=R{R}-S{R}")
    C.cell(row=r, column=21, value=f"=J{R}+R{R}")
    C.cell(row=r, column=23, value=f'=IF((I{R}+J{R}+P{R})/2<1000,"n/m",(SUMIFS({rng("W")},{q},{rng("H")},"Stocked")+SUMIFS({rng("W")},{q},{rng("H")},"Hybrid"))/((I{R}+J{R}+P{R})/2))')
    C.cell(row=r, column=26, value=f"=F{R}*Assumptions!$E${ROT_ROW[cat]}*(1+{g})")
    C.cell(row=r, column=27, value=f"=L{R}+Z{R}")
    C.cell(row=r, column=24, value=f"=SUMIFS({rng('AI')},{q})+G{R}*Assumptions!$E${ROT_ROW[cat]}*(1+{gL})")
    C.cell(row=r, column=25, value=f"=SUMIFS({rng('AJ')},{q})+G{R}*Assumptions!$E${ROT_ROW[cat]}*(1+{gH})")
# unattributed row
ur = cr + len(CATS)
CAT_ROW["Unattributed"] = ur
U = str(ur)
C.cell(row=ur, column=1, value="Unattributed sales (no SKU / custom items)").font = F(bold=True)
C.cell(row=ur, column=1).comment = Comment("TTM line items with no SKU (deleted products, custom POS items). Projected at "
                                           "TTM COGS x (1 + growth), order-to-demand; no inventory held.", "Model")
C.cell(row=ur, column=2, value=0)
C.cell(row=ur, column=3, value=f'=SUMIFS({XR("G")},{XR("E")},"Unattributed")')
C.cell(row=ur, column=4, value=f'=SUMIFS({XR("H")},{XR("E")},"Unattributed")')
C.cell(row=ur, column=5, value=f'=SUMIFS({XR("I")},{XR("E")},"Unattributed")')
C.cell(row=ur, column=6, value=0); C.cell(row=ur, column=7, value=0)
C.cell(row=ur, column=8, value=f"=IFERROR(1-(E{U}+G{U})/(D{U}+F{U}),0)")
for col in (9, 10, 14, 16, 17, 19):
    C.cell(row=ur, column=col, value=0)
C.cell(row=ur, column=11, value=f"=C{U}*(1+{g})")
C.cell(row=ur, column=12, value=f"=D{U}*(1+{g})")
C.cell(row=ur, column=13, value=f"=E{U}*(1+{g})")
C.cell(row=ur, column=15, value=f"=M{U}+N{U}")
C.cell(row=ur, column=18, value=f"=M{U}")
C.cell(row=ur, column=20, value=f"=R{U}-S{U}")
C.cell(row=ur, column=21, value=f"=J{U}+R{U}")
C.cell(row=ur, column=23, value=0)
C.cell(row=ur, column=24, value=f"=E{U}*(1+{gL})")
C.cell(row=ur, column=25, value=f"=E{U}*(1+{gH})")
C.cell(row=ur, column=26, value=0)
C.cell(row=ur, column=27, value=f"=L{U}+Z{U}")
tr = ur + 1
T = str(tr)
C.cell(row=tr, column=1, value="TOTAL").font = F(bold=True)
for col in range(2, 28):
    if col in (8, 22, 23):
        continue
    C.cell(row=tr, column=col, value=f"=SUM({CL(col)}{cr}:{CL(col)}{ur})")
C.cell(row=tr, column=8, value=f"=IFERROR(1-(E{T}+G{T})/(D{T}+F{T}),0)")
C.cell(row=tr, column=23, value=f'=IF((I{T}+J{T}+P{T})/2<1000,"n/m",(SUMIFS({rng("W")},{rng("H")},"Stocked")+SUMIFS({rng("W")},{rng("H")},"Hybrid"))/((I{T}+J{T}+P{T})/2))')
C.cell(row=CH, column=23).comment = Comment("Stocked + Hybrid projected COGS / average owned inventory (beginning on-hand + open POs, "
                                            "and target ending). n/m where average owned inventory < $1,000 (category is "
                                            "essentially drop-ship).", "Model")
for r in range(cr, tr + 1):
    C.cell(row=r, column=22, value=f"=IFERROR(U{r}/$U${tr},0)")
    for col, fmt in enumerate([None, NUM, NUM, USD, USD, USD, USD, PCT, USD, USD, NUM, USD, USD, USD, USD, USD, USD, USD,
                               USD, USD, USD, PCT, '0.0"x"', USD, USD, USD, USD], 1):
        cell = C.cell(row=r, column=col)
        if fmt:
            cell.number_format = fmt
        cell.border = BOX
        if r == tr:
            cell.font = F(bold=True); cell.fill = TOT_FILL; cell.border = TOP2
C.freeze_panes = "B6"

# memo / reconciliation block
m0 = tr + 2
C.cell(row=m0, column=1, value="Reconciliation to Shopify TTM net sales").font = F(bold=True, size=11, color="1F3864")
memo = [
    ("Active SKUs (SKU Detail)", f"=D{T}-D{U}"),
    ("Retired SKUs (Exclusions - replaced via rotation allowance)", f"=F{T}"),
    ("Unattributed - no SKU (Exclusions)", f"=D{U}"),
    ("Net units <= 0, archived products (Exclusions)",
     f'=SUMIFS({XR("H")},{XR("F")},"Net units <= 0 over TTM (returns exceed sales)")+SUMIFS({XR("H")},{XR("F")},"Product archived in Shopify")'),
    ("Non-inventory: memberships, gift cards, protection fees, digital (Exclusions)",
     f'=SUMIFS({XR("H")},{XR("F")},"Non-inventory (membership / gift card / protection fee / digital download)")'),
]
for i, (lab, fml) in enumerate(memo):
    r = m0 + 1 + i
    C.cell(row=r, column=1, value=lab)
    c = C.cell(row=r, column=4, value=fml); c.number_format = USD
rr = m0 + 1 + len(memo)
C.cell(row=rr, column=1, value="Total TTM net sales (model)").font = F(bold=True)
C.cell(row=rr, column=4, value=f"=SUM(D{m0+1}:D{rr-1})").number_format = USD
C.cell(row=rr + 1, column=1, value="Shopify reported TTM net sales (control)")
c = C.cell(row=rr + 1, column=4, value=round(sum(m[1] for m in CTRL_MONTHS), 2))
c.font = F(color=BLUE); c.number_format = USD
c.comment = Comment("ShopifyQL: FROM sales SHOW net_sales TIMESERIES month SINCE 2025-11-01 UNTIL 2026-10-31 (pulled 2026-11-12).", "Source")
C.cell(row=rr + 2, column=1, value="Difference").font = F(bold=True)
c = C.cell(row=rr + 2, column=4, value=f"=D{rr}-D{rr+1}"); c.number_format = USD2; c.font = F(bold=True)
C.cell(row=rr + 3, column=1, value="Notes: Purchases are stated at Linda's current landed unit cost. 'New Purchases' excludes open POs "
       "already placed (shown separately). Stocked/Hybrid = inventory Linda's will own and hold; Dropship/Order-to-Demand = "
       "purchased only as customer orders arrive (no inventory held).").font = F(italic=True, size=9)
C.merge_cells(start_row=rr + 3, start_column=1, end_row=rr + 3, end_column=14)
C.cell(row=rr + 3, column=1).alignment = WRAP
C.row_dimensions[rr + 3].height = 30

# bridge: TTM COGS -> projected COGS -> new purchases
b0 = rr + 5
C.cell(row=b0, column=1, value="Bridge: trailing-12-month COGS to projected purchases (at cost)").font = F(bold=True, size=11, color="1F3864")
L_, P_, T_, N_ = rng("L"), rng("P"), rng("T"), rng("N")
bridge = [
    ("TTM cost of goods sold (Shopify)", f"={SK}N3+Exclusions!I3"),
    ("Less: non-inventory, returns-only and archived items", f"=-(Exclusions!I3-G{T}-E{U})"),
    ("Less: retired SKUs (no sales in last 91 days)", f"=-G{T}"),
    ("TTM COGS of continuing SKUs + unattributed", f"=E{T}"),
    ("Cost update: TTM average cost -> current Shopify unit cost", f"=SUMPRODUCT({L_},{P_})-SUM({N_})"),
    ("Declining SKUs projected at lower last-91-day run-rate", f"=SUMPRODUCT({T_},{P_})-SUMPRODUCT({L_},{P_})"),
    ("Demand growth at base-case rate", f"={g}*(SUMPRODUCT({T_},{P_})+E{U})"),
    ("Assortment rotation allowance (new SKUs replacing retired)", f"=N{T}"),
    ("Projected 12-month COGS", None),
    ("Plus: target ending owned inventory", f"=P{T}"),
    ("Less: owned inventory on hand today", f"=-I{T}"),
    ("Less: open purchase orders already placed", f"=-J{T}"),
    ("Plus: excess stock not usable within 12 months (not credited)", f"=Q{T}"),
    ("Projected NEW purchases (base case)", None),
]
for i, (lab, fml) in enumerate(bridge):
    r = b0 + 1 + i
    C.cell(row=r, column=1, value=lab)
    if lab == "Projected 12-month COGS":
        fml = f"=SUM(D{b0+4}:D{r-1})"
    if lab.startswith("Projected NEW"):
        fml = f"=SUM(D{b0+9}:D{r-1})"
    c = C.cell(row=r, column=4, value=fml); c.number_format = USD
    if lab.startswith(("Projected", "TTM COGS of")):
        C.cell(row=r, column=1).font = F(bold=True); c.font = F(bold=True); c.border = Border(top=thin)
BR_COGS = f"D{b0+9}"
BR_PUR = f"D{b0+14}"
C.cell(row=b0 + 9, column=5, value=f'=IF(ABS({BR_COGS}-O{T})<1,"ties to Total Proj 12M COGS","CHECK")').font = F(italic=True, size=9)
C.cell(row=b0 + 14, column=5, value=f'=IF(ABS({BR_PUR}-R{T})<1,"ties to New Purchases - Base Case","CHECK")').font = F(italic=True, size=9)

# ====================================================================== Monthly Projection
M = wb.create_sheet("Monthly Projection", 1)
title(M, "Monthly Projection by Category - Nov 2026 to Oct 2027 (at cost)",
      "COGS phased by last year's same-month share; new purchases = COGS + change in owned inventory. 12-month totals tie to Category Summary.")
M.column_dimensions["A"].width = 40
for j in range(2, 16):
    M.column_dimensions[CL(j)].width = 12
CS = "'Category Summary'!"
rows_all = CATS + ["Unattributed"]
labels_all = CATS + ["Unattributed sales (no SKU)"]


def block(r_start, heading, cell_fn, fmt=USD, total=True):
    M.cell(row=r_start, column=1, value=heading).font = F(bold=True, size=11, color="1F3864")
    h = r_start + 1
    for j, lab in enumerate(["Category"] + mon_labels + ["12M Total"]):
        c = M.cell(row=h, column=1 + j, value=lab)
        c.font = F(bold=True, color="FFFFFF"); c.fill = HDR_FILL; c.alignment = CENTER
    out_rows = {}
    for i, cat in enumerate(rows_all):
        r = h + 1 + i
        out_rows[cat] = r
        M.cell(row=r, column=1, value=labels_all[i])
        for m in range(12):
            c = M.cell(row=r, column=2 + m, value=cell_fn(cat, m, r))
            c.number_format = fmt
        c = M.cell(row=r, column=14, value=f"=SUM(B{r}:M{r})" if total else None)
        c.number_format = fmt; c.font = F(bold=True)
    t = h + 1 + len(rows_all)
    M.cell(row=t, column=1, value="Total").font = F(bold=True)
    for col in range(2, 15):
        c = M.cell(row=t, column=col, value=f"=SUM({CL(col)}{h+1}:{CL(col)}{t-1})")
        c.number_format = fmt; c.font = F(bold=True); c.fill = TOT_FILL; c.border = TOP2
    return out_rows, t


PH = lambda cat, m: f"Assumptions!${CL(2+m)}${PHASE_ROW[cat]}"
cogs_rows, cogs_t = block(4, "1. Projected cost of goods sold (all fulfillment models)",
                          lambda cat, m, r: f"={CS}$O${CAT_ROW[cat]}*{PH(cat, m)}")
b2 = cogs_t + 3


def end_inv(cat, m, r):
    tgt = f"{CS}$P${CAT_ROW[cat]}"
    if m == 11:
        return f"={tgt}"
    return f"={tgt}*12*{PH(cat, m+1)}"


inv_rows, inv_t = block(b2, "2. Owned inventory at month-end (Stocked + Hybrid SKUs; target cover, seasonally adjusted)",
                        end_inv, total=False)
for r in list(inv_rows.values()) + [inv_t]:
    M.cell(row=r, column=14, value=f"=M{r}")
M.cell(row=b2 + 1, column=14, value="Ending")
# beginning usable inventory column note
b3 = inv_t + 3


def purch(cat, m, r):
    cg = f"{CL(2+m)}{cogs_rows[cat]}"
    endc = f"{CL(2+m)}{inv_rows[cat]}"
    if m == 0:
        beg = f"({CS}$I${CAT_ROW[cat]}+{CS}$J${CAT_ROW[cat]}-{CS}$Q${CAT_ROW[cat]})"
    else:
        beg = f"{CL(1+m)}{inv_rows[cat]}"
    return f"={cg}+{endc}-{beg}"


pur_rows, pur_t = block(b3, "3. Projected new purchases (COGS + ending inventory - beginning usable inventory; excludes open POs)", purch)
b4 = pur_t + 2
M.cell(row=b4, column=1, value="Beginning usable owned inventory (on-hand + open POs - excess)").font = F(italic=True)
c = M.cell(row=b4, column=2, value=f"={CS}I{tr}+{CS}J{tr}-{CS}Q{tr}"); c.number_format = USD; c.font = F(color=GREEN)
M.cell(row=b4 + 1, column=1, value="Check: 12M new purchases vs Category Summary (should be 0)").font = F(bold=True)
c = M.cell(row=b4 + 1, column=2, value=f"=ROUND(N{pur_t}-{CS}R{tr},0)"); c.number_format = USD
c = M.cell(row=b4 + 2, column=1, value="Check: 12M COGS vs Category Summary (should be 0)"); c.font = F(bold=True)
c = M.cell(row=b4 + 2, column=2, value=f"=ROUND(N{cogs_t}-{CS}O{tr},0)"); c.number_format = USD
M.freeze_panes = "B4"
MON_PUR_CHECK = f"'Monthly Projection'!B{b4+1}"
MON_COGS_CHECK = f"'Monthly Projection'!B{b4+2}"

# ====================================================================== Vendor & AP tie-out
V = wb.create_sheet("Vendor & AP Tie-Out")
title(V, "Vendor Summary and Bill.com Accounts-Payable Tie-Out",
      "Shopify COGS by vendor vs. vendor bills entered in Bill.com (same 12-month window, by bill created date). "
      "Coverage below 100% = vendor paid outside Bill.com (card / ACH / auto-debit) or billed through a factor.")
BILL_MAP = [  # (Bill.com name contains, group)
    ("hobbs leasing", "NON-INVENTORY"), ("brewer", "Brewer"), ("shannon", "Shannon Fabrics"), ("moda", "Moda Fabrics & Supplies"),
    ("pellon", "Pellon"), ("hobbs", "Hobbs Bonded Fibers"), ("northcott", "Northcott"), ("milberg", "Jaftex (Studio E / Blank / Henry Glass)"),
    ("checker", "Checker Distributor"), ("rnk", "Rnk Distributing"), ("riley blake", "Riley Blake Designs"),
    ("quilters dream", "Quilters Dream Batting"), ("schenck", "EE Schenck Co"), ("warm", "Warm Company"),
    ("superior threads", "Superior Threads"), ("qt fabrics", "Quilting Treasures Fabric"), ("pqw", "Pauline's Quilters World"),
    ("fil-tec", "Fil-Tec"), ("timeless", "Timeless Treasures"), ("airlite", "Air Lite Manufacturing"), ("air lite", "Air Lite Manufacturing"),
    ("michael miller", "Michael Miller Fabrics"), ("aurifil", "Aurifil"), ("marcus", "Marcus Fabrics"), ("yli", "YLI"),
    ("superior sewing", "Superior Sewing Machines & Supply"), ("marshall", "Marshall Dry Goods"), ("dear stella", "Dear Stella"),
    ("benartex", "Benartex Inc"), ("wildflower", "Wildflower Quilting"), ("choice fabrics", "Choice Fabrics"),
    ("textile collections", "Textile Collections"), ("andover", "Andover Fabrics"), ("windham", "Windham Fabrics"),
    ("free spirit", "Free Spirit Fabrics"), ("p&b", "P&B Textiles"), ("hoffman", "Hoffman California Fabrics"),
    ("united notions", "United Notions"), ("famore", "Famore"), ("wonderfil", "WonderFil USA"), ("cutterpillar", "CutterPillar"),
    ("sewtites", "SewTites"), ("fabric company", "The Fabric Company"), ("high country", "High Country Quilts"),
    ("legit kits", "Legit Kits"), ("singer", "Singer"), ("poppie", "Poppie Cotton"),
    ("cit group", "FACTOR - CIT (mill not identified on bill)"), ("rosenthal", "FACTOR - Rosenthal (mill not identified)"),
    ("slr business", "FACTOR - SLR Business Credit (mill not identified)"),
]
NONINV_KEYS = ("fed ex", "fedex", "texas container", "impact tech", "escalon", "trinity logistics", "allied central", "truecustomer",
               "karra law", "mckinney maids", "seko", "uline", "archive supply", "jarom thurston", "daryl gordon", "dianna heiner",
               "ups", "usps", "shipstation", "insurance", "atmos", "verizon", "att")
SHOP_GROUP = {"Brewer Distributor": "Brewer", "Brewer Sewing": "Brewer", "Linda's Electric Quilters": "Hobbs Bonded Fibers",
              "Studio E Fabrics": "Jaftex (Studio E / Blank / Henry Glass)", "Blank Quilting Inc": "Jaftex (Studio E / Blank / Henry Glass)",
              "Henry Glass & Co": "Jaftex (Studio E / Blank / Henry Glass)"}


def bill_group(name):
    n = name.lower()
    for k, grp in BILL_MAP:
        if k in n:
            return grp
    if any(k in n for k in NONINV_KEYS):
        return "NON-INVENTORY"
    return "UNMAPPED - review"


# Bill.com went live 2026-05-29 (go-live batch includes backlog invoices back to Sep-2025), so compare
# bills with INVOICE DATE Jun 1 - Oct 31 2026 against Shopify COGS for the same five months.
W0, W1 = "2026-06-01", "2026-10-31"
bt = {}
for b in d["bills"]["ttm"]:
    grp = bill_group(b["vendor"])
    e = bt.setdefault(grp, {"win": 0.0, "all": 0.0, "n": 0, "names": set(), "due": 0.0})
    idate = b["inv_date"] or b["created"]
    e["all"] += b["amount"]; e["due"] += b["due"]; e["names"].add(b["vendor"])
    if W0 <= idate <= W1:
        e["win"] += b["amount"]; e["n"] += 1
jo = json.load(open(S + "data/jun_oct_vendor_sku.json"))["rows"]
shop = {}
for x in skus + excl:
    grp = SHOP_GROUP.get(x["vendor"], x["vendor"] or "(blank vendor)")
    shop.setdefault(grp, {"cogs": 0.0, "win": 0.0})
    shop[grp]["cogs"] += x["cogs"]
for vend, sk, net, cogs in jo:
    grp = SHOP_GROUP.get(vend, vend or "(blank vendor)")
    shop.setdefault(grp, {"cogs": 0.0, "win": 0.0})
    shop[grp]["win"] += float(cogs or 0)
vrows = sorted(set(list(shop.keys()) + [k for k in bt if k not in ("NON-INVENTORY", "UNMAPPED - review")]),
               key=lambda k: -(shop.get(k, {}).get("cogs", 0) + bt.get(k, {}).get("all", 0)))
top_v = vrows[:45]
other_v = vrows[45:]
vcols = [("Vendor (grouped)", 38), ("TTM Shopify COGS $ (Nov-25 to Oct-26)", 14), ("Proj 12M New Purchases $ (SKU level)", 14),
         ("Shopify COGS $ Jun-Oct 2026", 14), ("Bill.com Bills $ - invoice date Jun-Oct 2026", 14), ("# Bills Jun-Oct", 8),
         ("Bill.com / Shopify COGS (Jun-Oct)", 10), ("All Bill.com Bills since go-live $ (incl. backlog)", 14),
         ("Open AP Due $", 12), ("Bill.com payee names", 60)]
header_row(V, 4, [c[0] for c in vcols], [c[1] for c in vcols], height=60)
vr = 5
VEND_GROUPS_REVERSE = {}
for k, v in SHOP_GROUP.items():
    VEND_GROUPS_REVERSE.setdefault(v, []).append(k)
EMPTY = {"win": 0, "all": 0, "n": 0, "due": 0, "names": set()}
sku_vendors = {x["vendor"] for x in skus}
for i, grp in enumerate(top_v):
    r = vr + i
    V.cell(row=r, column=1, value=grp)
    members = VEND_GROUPS_REVERSE.get(grp, []) + ([grp] if grp in sku_vendors else [])
    fml = "+".join(f'SUMIFS({rng("AE")},{rng("E")},"{mname}")' for mname in members if mname in sku_vendors) or "0"
    V.cell(row=r, column=3, value="=" + fml)
    e = bt.get(grp, EMPTY)
    for col, val in ((2, shop.get(grp, {}).get("cogs", 0)), (4, shop.get(grp, {}).get("win", 0)), (5, e["win"]), (6, e["n"]),
                     (8, e["all"]), (9, e["due"])):
        c = V.cell(row=r, column=col, value=round(val, 2)); c.font = F(color=BLUE)
    V.cell(row=r, column=7, value=f"=IFERROR(E{r}/D{r},0)")
    V.cell(row=r, column=10, value="; ".join(sorted(e["names"])))
r_other = vr + len(top_v)
V.cell(row=r_other, column=1, value=f"All other vendors ({len(other_v)})")
V.cell(row=r_other, column=3, value=f"={CS}R{tr}-{CS}N{tr}-{CS}R{ur}-SUM(C{vr}:C{r_other-1})")
for col, val in ((2, sum(shop.get(k, {}).get("cogs", 0) for k in other_v)), (4, sum(shop.get(k, {}).get("win", 0) for k in other_v)),
                 (5, sum(bt.get(k, EMPTY)["win"] for k in other_v)), (6, sum(bt.get(k, EMPTY)["n"] for k in other_v)),
                 (8, sum(bt.get(k, EMPTY)["all"] for k in other_v)), (9, sum(bt.get(k, EMPTY)["due"] for k in other_v))):
    c = V.cell(row=r_other, column=col, value=round(val, 2)); c.font = F(color=BLUE)
V.cell(row=r_other, column=7, value=f"=IFERROR(E{r_other}/D{r_other},0)")
r_sub = r_other + 1
V.cell(row=r_sub, column=1, value="Subtotal - inventory vendors")
for col in (2, 3, 4, 5, 6, 8, 9):
    V.cell(row=r_sub, column=col, value=f"=SUM({CL(col)}{vr}:{CL(col)}{r_other})")
V.cell(row=r_sub, column=7, value=f"=IFERROR(E{r_sub}/D{r_sub},0)")
extra = [("UNMAPPED - review", "Bill.com payees not matched to a Shopify vendor"),
         ("NON-INVENTORY", "Freight, rent, leases, services (excluded from tie-out)")]
for i, (k, lab) in enumerate(extra):
    r = r_sub + 1 + i
    e = bt.get(k, EMPTY)
    V.cell(row=r, column=1, value=lab)
    for col, val in ((5, e["win"]), (6, e["n"]), (8, e["all"]), (9, e["due"])):
        c = V.cell(row=r, column=col, value=round(val, 2)); c.font = F(color=BLUE)
    V.cell(row=r, column=10, value="; ".join(sorted(e["names"])))
r_tot = r_sub + 3
V.cell(row=r_tot, column=1, value="Total Bill.com bills")
for col in (5, 6, 8, 9):
    V.cell(row=r_tot, column=col, value=f"=SUM({CL(col)}{r_sub}:{CL(col)}{r_sub+2})")
for r in range(vr, r_tot + 1):
    for col, fmt in ((2, USD), (3, USD), (4, USD), (5, USD), (6, NUM), (7, PCT), (8, USD), (9, USD)):
        V.cell(row=r, column=col).number_format = fmt
    if r in (r_sub, r_tot):
        for col in range(1, 11):
            V.cell(row=r, column=col).font = F(bold=True)
            V.cell(row=r, column=col).fill = TOT_FILL
V.freeze_panes = "B5"
V.cell(row=r_tot + 2, column=1, value="Reading this table: Bill.com went live 2026-05-29, so the like-for-like comparison is invoice date Jun-Oct 2026 vs Shopify COGS Jun-Oct 2026. Bills reflect purchases (incl. stock build), COGS reflects sales, so timing differs by vendor. Drop-ship distributors (e.g., Checker) "
       "and card-paid vendors are under-represented; factored mills (Jaftex via Milberg, CIT, Rosenthal, SLR) appear under the factor's "
       "name. Bill.com totals include freight/terms differences vs. Shopify COGS, which uses the unit cost on each SKU.").font = F(italic=True, size=9)
V.merge_cells(start_row=r_tot + 2, start_column=1, end_row=r_tot + 2, end_column=10)
V.cell(row=r_tot + 2, column=1).alignment = WRAP
V.row_dimensions[r_tot + 2].height = 40
AP_SUB = f"'Vendor & AP Tie-Out'!E{r_sub}"
AP_TOT = f"'Vendor & AP Tie-Out'!H{r_tot}"
AP_COGS = f"'Vendor & AP Tie-Out'!D{r_sub}"

# ====================================================================== Data Vetting
Q = wb.create_sheet("Data Vetting")
title(Q, "Data Vetting & Reconciliation", "Each check recalculates. Control totals (blue) are from the source system named in the Source column.")
qcols = [("#", 5), ("Check", 58), ("Model Value", 16), ("Control Value", 16), ("Difference", 14), ("Status", 10), ("Source / Explanation", 80)]
header_row(Q, 4, [c[0] for c in qcols], [c[1] for c in qcols])
ctrl_net = round(sum(m[1] for m in CTRL_MONTHS), 2)
ctrl_cogs = round(sum(m[2] for m in CTRL_MONTHS), 2)
ctrl_units = sum(m[3] for m in CTRL_MONTHS)
active_cogs = f"{CS}E{tr}-{CS}E{ur}"
checks = [
    ("TTM net sales: SKU Detail + Exclusions = Shopify total", f"={SK}M3+Exclusions!H3", ctrl_net, "tie",
     "ShopifyQL FROM sales SHOW net_sales, Nov-2025..Oct-2026. Every dollar of sales is either projected or listed in Exclusions."),
    ("TTM COGS: SKU Detail + Exclusions = Shopify total", f"={SK}N3+Exclusions!I3", ctrl_cogs, "tie",
     "ShopifyQL FROM sales SHOW cost_of_goods_sold, same window. Small differences arise from rounding of SKU-level cost."),
    ("TTM units: SKU Detail + Exclusions = Shopify total", f"={SK}L3+Exclusions!G3", ctrl_units, "tie",
     "ShopifyQL FROM sales SHOW net_items_sold, same window."),
    ("12-month new purchases: Monthly Projection = Category Summary", f"={MON_PUR_CHECK}", 0, "tie",
     "Monthly roll-forward (COGS + ending inventory - beginning) must equal SKU-level total plus rotation allowance."),
    ("12-month COGS: Monthly Projection = Category Summary", f"={MON_COGS_CHECK}", 0, "tie", "Monthly phasing shares sum to 100% per category."),
    ("COGS bridge ties to Category Summary projected COGS", f"={CS}{BR_COGS}", f"={CS}O{tr}", "tie",
     "Bridge on Category Summary: TTM COGS -> exclusions -> cost update -> declining SKUs -> growth -> rotation."),
    ("Purchases bridge ties to Category Summary new purchases", f"={CS}{BR_PUR}", f"={CS}R{tr}", "tie",
     "Projected COGS + target ending inventory - on hand - open POs + excess = new purchases."),
    ("Monthly phasing sums to 100% (all categories)",
     f"=SUM(Assumptions!N{PHASE_ROW[CATS[0]]}:N{PHASE_ROW['Unattributed']})", len(CATS) + 1, "tie", "Each row of the phasing table = 100%."),
    ("Active SKU count: Category Summary = SKU Detail rows", f"={CS}B{tr}", len(skus), "tie", "COUNTIFS by category covers every SKU row."),
    ("Share of active-SKU TTM COGS with location-verified owned inventory",
     f'=SUMIFS({rng("N")},{rng("I")},"Y")/({active_cogs})', 0.75, "min",
     "Top SKUs by COGS were checked one-by-one at Linda's 4 owned Shopify locations. Unverified tail is modeled "
     "order-to-demand (no stock build and no on-hand credit)."),
    ("Share of active-SKU TTM COGS using estimated (missing) cost", f'=SUMIFS({rng("N")},{rng("Q")},"Estimated (no cost on file)")/({active_cogs})',
     0.02, "max", "SKUs with no cost in Shopify are costed at their category's TTM COGS / net sales ratio."),
    ("SKUs where unit cost exceeds average net selling price (count)", f'=COUNTIFS({rng("AK")},"*Unit cost exceeds*")', 0, "info",
     "Listed in SKU Detail 'Data Flags' - review cost records before submission."),
    ("Owned on-hand inventory at cost (verified SKUs)", f"={CS}I{tr}", None, "info",
     "Units at Linda's own locations x current unit cost."),
    ("Shopify-reported inventory value, ALL locations incl. vendor feeds (NOT USED)", SHOPIFY_INV_VALUE_ALL, None, "info",
     f"ShopifyQL FROM inventory SHOW ending_inventory_value, 2026-11-12: {SHOPIFY_INV_UNITS_ALL:,} units. Inflated by vendor "
     "drop-ship feed quantities (e.g., single SKUs with 4-5 million units). Not a valid measure of Linda's inventory."),
    ("Bill.com inventory-vendor bills / Shopify COGS, Jun-Oct 2026 (AP coverage)", f"=IFERROR({AP_SUB}/{AP_COGS},0)", 0.5, "min",
     "Bill.com Payables went live 2026-05-29; bills by invoice date Jun 1-Oct 31 2026 vs ShopifyQL COGS same months. Coverage <100% expected: card/ACH-paid and drop-ship vendors."),
    ("Bill.com total bills since go-live (all payees, incl. backlog)", f"={AP_TOT}", None, "info", "2,060 bills created 2026-05-29..2026-10-30. Includes freight, rent, leases and services."),
    ("Projected purchases at base case vs TTM COGS (growth sanity)", f"=IFERROR({CS}U{tr}/{CS}E{tr}/(1+{g})-1,0)", None, "info",
     "Purchase requirement above TTM COGS x growth comes from inventory build to target cover; below it from using existing stock."),
]
for i, (lab, model, ctrl, kind, src) in enumerate(checks):
    r = 5 + i
    Q.cell(row=r, column=1, value=i + 1)
    Q.cell(row=r, column=2, value=lab).alignment = WRAP
    c = Q.cell(row=r, column=3, value=model)
    if not str(model).startswith("="):
        c.font = F(color=BLUE)
    if ctrl is not None:
        c2 = Q.cell(row=r, column=4, value=ctrl); c2.font = F(color=GREEN if str(ctrl).startswith("=") else BLUE)
    if kind == "tie":
        Q.cell(row=r, column=5, value=f"=C{r}-D{r}")
        Q.cell(row=r, column=6, value=f'=IF(ABS(E{r})<=MAX(1,ABS(D{r})*0.0001),"PASS","REVIEW")')
    elif kind == "min":
        Q.cell(row=r, column=6, value=f'=IF(C{r}>=D{r},"PASS","REVIEW")')
        Q.cell(row=r, column=4).comment = Comment("Minimum acceptable threshold.", "Model")
    elif kind == "max":
        Q.cell(row=r, column=6, value=f'=IF(C{r}<=D{r},"PASS","REVIEW")')
        Q.cell(row=r, column=4).comment = Comment("Maximum acceptable threshold.", "Model")
    else:
        Q.cell(row=r, column=6, value="INFO")
    Q.cell(row=r, column=7, value=src).alignment = WRAP
    pct_rows = ("Share", "AP coverage", "growth sanity")
    is_pct = any(k in lab for k in pct_rows)
    is_int = lab.startswith(("Active SKU", "SKUs where", "Monthly phasing", "TTM units"))
    fmt = PCT if is_pct else (NUM if is_int else USD)
    if lab.startswith("Monthly phasing"):
        fmt = '0.00'
    for col in (3, 4, 5):
        Q.cell(row=r, column=col).number_format = fmt
    Q.row_dimensions[r].height = 42
    for col in range(1, 8):
        Q.cell(row=r, column=col).border = BOX
        Q.cell(row=r, column=col).alignment = WRAP if col in (2, 7) else Alignment(vertical="top")
qe = 5 + len(checks) - 1
green = PatternFill("solid", fgColor="C6EFCE"); red = PatternFill("solid", fgColor="FFC7CE")
Q.conditional_formatting.add(f"F5:F{qe}", CellIsRule(operator="equal", formula=['"PASS"'], fill=green))
Q.conditional_formatting.add(f"F5:F{qe}", CellIsRule(operator="equal", formula=['"REVIEW"'], fill=red))
VET_PASS = f'=COUNTIF(\'Data Vetting\'!F5:F{qe},"PASS")&" PASS / "&COUNTIF(\'Data Vetting\'!F5:F{qe},"REVIEW")&" REVIEW"'

# data quality exceptions summary
qx = qe + 3
Q.cell(row=qx, column=2, value="Data-quality exceptions in SKU Detail (see 'Data Flags' column)").font = F(bold=True, size=11, color="1F3864")
flag_kinds = ["Category inferred", "Stocked SKU currently at zero", "Negative owned on-hand", "SKU shared by",
              "Product status DRAFT", "Product status UNLISTED", "Accelerating", "Unit cost exceeds", "Cost estimated"]
for i, k in enumerate(flag_kinds):
    r = qx + 1 + i
    Q.cell(row=r, column=2, value=k)
    c = Q.cell(row=r, column=3, value=f'=COUNTIFS({rng("AK")},"*{k}*")'); c.number_format = NUM
    c = Q.cell(row=r, column=4, value=f'=SUMIFS({rng("N")},{rng("AK")},"*{k}*")'); c.number_format = USD
Q.cell(row=qx, column=3, value="SKUs").font = F(bold=True)
Q.cell(row=qx, column=4, value="TTM COGS $").font = F(bold=True)

# ====================================================================== Methodology
N = wb.create_sheet("Methodology")
title(N, "Methodology, Sources and Limitations")
N.column_dimensions["A"].width = 150
text = [
    ("PURPOSE", True),
    ("Projected 12-month inventory purchase requirement for Red River Quiltworks LLC dba Linda's Electric Quilters (lindas.com), "
     "built bottom-up at SKU level from actual purchasing (customer order) history and summarized by product category.", False),
    ("", False),
    ("DATA SOURCES (all pulled live on 2026-11-12)", True),
    ("1. Shopify Plus (lindas-electric-quilters.myshopify.com) - ShopifyQL sales by SKU: units, net sales, cost of goods sold, for "
     "Nov 1 2025 - Oct 31 2026 (trailing 12 months, 'TTM') and Aug 2 - Oct 31 2026 (last 91 days, 'L91').", False),
    ("2. Shopify Admin GraphQL - for the highest-COGS SKUs: current unit cost, product status, and on-hand / incoming quantities at each "
     "of Linda's four owned locations (McKinney TX store/warehouse, Springfield TN fulfillment center, Event Popup, Retail Popup).", False),
    ("3. Bill.com Payables - all 2,060 vendor bills (Bill.com went live 2026-05-29; earlier periods are not in Bill.com). Tie-out uses invoice dates Jun-Oct 2026.", False),
    ("", False),
    ("METHOD", True),
    ("Demand: Base annual units = TTM units. If a SKU's L91 run-rate (annualized) is below the declining-SKU threshold of TTM, the lower "
     "L91 run-rate is used. Growing SKUs are not uplifted. Projected units = base x (1 + growth). Seasonality comes from last year's same-month mix.", False),
    ("Cost: Shopify's current unit cost on the SKU; otherwise the SKU's TTM average COGS per unit; otherwise the category's COGS/sales ratio "
     "applied to the SKU's average net price (flagged).", False),
    ("Fulfillment model: Stocked (Linda's owns stock), Hybrid (Linda's stocks and vendor also drop-ships), Dropship (vendor ships direct; "
     "Linda's buys only when a customer orders), Not verified (tail SKUs not checked by location - modeled like Dropship).", False),
    ("Purchases: New purchase units = MAX(0, projected units + target ending stock - owned on-hand - open POs). Target ending stock "
     "applies only to Stocked/Hybrid SKUs. Inventory above the 12-month need is reported as Excess and is not credited elsewhere.", False),
    ("Assortment rotation: SKUs with TTM sales but no sales in the last 91 days are treated as retired and not projected. Their category "
     "volume is replaced by new SKUs at a measured replacement ratio (new-SKU run-rate vs retired volume, capped at 100%) times a haircut.", False),
    ("Unattributed: TTM sales with no SKU (deleted products / custom items) are projected at TTM COGS x (1 + growth), order-to-demand.", False),
    ("Excluded entirely: Crafter Club memberships, gift cards, package/shipping protection fees, and digital downloads - not inventory.", False),
    ("", False),
    ("KEY VETTING POINTS FOR THE LENDER", True),
    ("- Every TTM sales dollar is accounted for: projected SKUs + Exclusions sheet reconcile to Shopify's reported total (Data Vetting #1-3).", False),
    ("- Shopify's built-in inventory valuation report (~$10 billion) includes vendor drop-ship feed quantities and is NOT used. Only "
     "units physically at Linda's own locations are counted as owned inventory.", False),
    ("- The base case uses +10% growth against observed trailing growth well above that (see Assumptions), and declining SKUs are "
     "projected at their lower recent run-rate.", False),
    ("- Bill.com coverage of COGS is below 100% by design: drop-ship and card-paid vendors and factored mills are partly outside Bill.com; "
     "the tie-out sheet shows the gap by vendor.", False),
    ("", False),
    ("LIMITATIONS", True),
    ("- Open POs are taken from Shopify 'incoming' quantities at owned locations; POs not entered in Shopify are not included.", False),
    ("- Owned inventory is verified for the highest-COGS SKUs (see Data Vetting for the share); tail SKUs carry no on-hand credit and no stock build.", False),
    ("- Unit costs are Shopify cost-per-item values; freight-in and vendor discounts are not separately modeled.", False),
    ("- Projections are management estimates based on historical sales; actual results will vary.", False),
]
for i, (t, bold) in enumerate(text):
    c = N.cell(row=3 + i, column=1, value=t)
    c.font = F(bold=bold, size=11 if bold else 10, color="1F3864" if bold else "000000")
    c.alignment = Alignment(wrap_text=True, vertical="top")

# ====================================================================== Cover
K = wb.create_sheet("Cover", 0)
K.sheet_view.showGridLines = False
K.column_dimensions["A"].width = 4
K.column_dimensions["B"].width = 66
K.column_dimensions["C"].width = 22
K.column_dimensions["D"].width = 22
K["B2"] = "Linda's Electric Quilters"
K["B2"].font = F(bold=True, size=18, color="1F3864")
K["B3"] = "Projected Inventory Purchases - 12 Months, November 2026 to October 2027"
K["B3"].font = F(bold=True, size=13)
K["B4"] = "Red River Quiltworks LLC dba Linda's Electric Quilters  |  2001 Central Circle #103, McKinney, TX 75069  |  lindas.com"
K["B4"].font = F(size=10, color="595959")
K["B5"] = "Prepared for lender review. Data as of November 12, 2026."
K["B5"].font = F(italic=True, size=10, color="595959")
K["B7"] = "Headline figures (at cost)"
K["B7"].font = F(bold=True, size=12, color="1F3864")
K["C7"] = "Base case"
K["D7"] = "Range (downside - upside)"
for c in ("C7", "D7"):
    K[c].font = F(bold=True); K[c].alignment = CENTER
head = [
    ("Trailing-12-month net sales (Nov 2025 - Oct 2026)", f"={CS}D{tr}+{CS}F{tr}+{CS}D{rr-1}+{CS}D{rr-2}", None, USD),
    ("Trailing-12-month cost of goods sold", f"={SK}N3+Exclusions!I3", None, USD),
    ("Projected 12-month net sales (incl. rotation allowance)", f"={CS}AA{tr}", None, USD),
    ("Projected 12-month cost of goods sold (incl. rotation allowance)", f"={CS}O{tr}", None, USD),
    ("   change vs trailing-12-month COGS (see bridge on Category Summary)", f"={CS}O{tr}/({SK}N3+Exclusions!I3)-1", None, PCT),
    ("Owned inventory on hand today", f"={CS}I{tr}", None, USD),
    ("Open purchase orders (already placed)", f"={CS}J{tr}", None, USD),
    ("Target owned inventory at period end", f"={CS}P{tr}", None, USD),
    ("Projected NEW purchases over 12 months", f"={CS}R{tr}", f'=TEXT({CS}X{tr},"$#,##0")&" - "&TEXT({CS}Y{tr},"$#,##0")', USD),
    ("   of which inventory Linda's will own and hold (Stocked / Hybrid)", f"={CS}S{tr}", None, USD),
    ("   of which bought only against customer orders (Dropship / order-to-demand)", f"={CS}T{tr}", None, USD),
    ("Total purchase requirement (open POs + new purchases)", f"={CS}U{tr}", None, USD),
    ("Peak month of new purchases", f"=INDEX('Monthly Projection'!B{b3+1}:M{b3+1},MATCH(MAX('Monthly Projection'!B{pur_t}:M{pur_t}),'Monthly Projection'!B{pur_t}:M{pur_t},0))", f"=MAX('Monthly Projection'!B{pur_t}:M{pur_t})", None),
    ("Base-case demand growth assumption", f"={AS['g']}", f'=TEXT({AS["gL"]},"0%")&" - "&TEXT({AS["gH"]},"0%")', PCT),
    ("Data vetting checks", VET_PASS, None, None),
]
for i, (lab, f1, f2, fmt) in enumerate(head):
    r = 8 + i
    K.cell(row=r, column=2, value=lab).font = F(bold=lab.startswith(("Projected NEW", "Total purchase")))
    c = K.cell(row=r, column=3, value=f1)
    c.font = F(color=GREEN, bold=lab.startswith(("Projected NEW", "Total purchase")))
    c.alignment = Alignment(horizontal="right")
    if fmt:
        c.number_format = fmt
    if f2:
        c2 = K.cell(row=r, column=4, value=f2); c2.font = F(color=GREEN); c2.alignment = Alignment(horizontal="right")
        if lab.startswith("Peak"):
            c2.number_format = USD
    for col in (2, 3, 4):
        K.cell(row=r, column=col).border = Border(bottom=thin)
c0 = 8 + len(head) + 1
K.cell(row=c0, column=2, value="Summary by product category (at cost unless noted)").font = F(bold=True, size=12, color="1F3864")
ctab = [("Product Category", "A"), ("TTM Net Sales $", None), ("TTM COGS $", None), ("Owned On-Hand $", "I"),
        ("Proj 12M COGS $", "O"), ("New Purchases $", "R"), ("% of New Purchases", None)]
for j, (lab, _) in enumerate(ctab):
    c = K.cell(row=c0 + 1, column=2 + j, value=lab)
    c.font = F(bold=True, color="FFFFFF"); c.fill = HDR_FILL; c.alignment = CENTER
K.row_dimensions[c0 + 1].height = 30
for j in range(3, 9):
    K.column_dimensions[CL(j)].width = 16
for i, key in enumerate(CATS + ["Unattributed", "TOTAL"]):
    r = c0 + 2 + i
    src = tr if key == "TOTAL" else CAT_ROW[key]
    vals = [f"={CS}A{src}", f"={CS}D{src}+{CS}F{src}", f"={CS}E{src}+{CS}G{src}", f"={CS}I{src}", f"={CS}O{src}",
            f"={CS}R{src}", f"=IFERROR({CS}R{src}/{CS}R{tr},0)"]
    for j, v in enumerate(vals):
        c = K.cell(row=r, column=2 + j, value=v)
        c.font = F(color=GREEN, bold=(key == "TOTAL"))
        c.number_format = PCT if j == 6 else USD
        c.border = TOP2 if key == "TOTAL" else Border(bottom=thin)
        if key == "TOTAL":
            c.fill = TOT_FILL
K.cell(row=c0 + 2 + len(CATS) + 2, column=2, value="TTM figures include retired SKUs; projections replace them via the rotation "
       "allowance. Non-inventory items (memberships, gift cards, fees, digital) are excluded throughout.").font = F(italic=True, size=8)
s0 = c0 + len(CATS) + 6
K.cell(row=s0, column=2, value="Workbook contents").font = F(bold=True, size=12, color="1F3864")
contents = [
    ("Category Summary", "Bank summary: TTM actuals, owned inventory, projected COGS and purchases by product category."),
    ("Monthly Projection", "Month-by-month COGS, owned inventory and new purchases by category."),
    ("SKU Detail", f"{len(skus):,} active SKUs with history, cost, on-hand, open POs and live projection formulas."),
    ("Assumptions", "Every input in one place (growth, cover days, decline rule, rotation haircut) plus seasonality."),
    ("Vendor & AP Tie-Out", "Shopify COGS vs Bill.com vendor bills by vendor."),
    ("Exclusions", f"{len(excl)+1:,} SKUs/lines not projected individually, each with its reason."),
    ("Data Vetting", "Reconciliations to source control totals with PASS/REVIEW status; data-quality exceptions."),
    ("Methodology", "Sources, method, lender vetting points and limitations."),
]
for i, (sh, desc) in enumerate(contents):
    r = s0 + 1 + i
    c = K.cell(row=r, column=2, value=sh)
    c.hyperlink = f"#'{sh}'!A1"
    c.font = F(color="0563C1", underline="single")
    K.cell(row=r, column=3, value=desc).font = F(size=9)
sg = s0 + len(contents) + 3
K.cell(row=sg, column=2, value="Management certification").font = F(bold=True, size=12, color="1F3864")
K.cell(row=sg + 1, column=2, value="The projections above are management's good-faith estimates based on the company's actual sales and "
       "inventory records as of the date shown.").font = F(size=9)
K.merge_cells(start_row=sg + 1, start_column=2, end_row=sg + 1, end_column=4)
K.cell(row=sg + 1, column=2).alignment = WRAP
K.row_dimensions[sg + 1].height = 28
for i, lab in enumerate(["Prepared by:", "Title:", "Signature / Date:", "Reviewed by:"]):
    r = sg + 3 + i * 2
    K.cell(row=r, column=2, value=lab).font = F(bold=True)
    for col in (3, 4):
        K.cell(row=r, column=col).border = Border(bottom=Side(style="thin", color="000000"))

# sheet order & tab colors
order = ["Cover", "Category Summary", "Monthly Projection", "SKU Detail", "Assumptions", "Vendor & AP Tie-Out", "Exclusions",
         "Data Vetting", "Methodology"]
wb._sheets = [wb[n] for n in order]
for n, col in zip(order, ["1F3864", "1F3864", "1F3864", "2E75B6", "FFC000", "70AD47", "A5A5A5", "C00000", "A5A5A5"]):
    wb[n].sheet_properties.tabColor = col
for ws in wb.worksheets:
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.oddFooter.left.text = "Linda's Electric Quilters - Projected Inventory Purchases Nov 2026-Oct 2027"
    ws.oddFooter.right.text = "Page &P of &N"
C.print_title_rows = "5:5"
C.page_setup.fitToWidth = 2
C.print_title_cols = "A:A"
W.print_title_rows = "4:4"
wb.active = 0
wb.save(OUT)
print("saved", OUT, "skus", len(skus), "excl", len(excl))
