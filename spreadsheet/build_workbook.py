"""Build the Home Loan Reality Check workbook v2 (Excel / Google Sheets).

The workbook implements the same approved Release 1.0 rules as the website
engine (PRODUCT_DECISIONS.md section 3, decisions D-04 and S-06). Its
repayment engine is checked against the golden scenarios in
reference/scenarios/ by spreadsheet/verify_workbook.py.

Usage (from the repository root):
    python3 -I spreadsheet/build_workbook.py [output.xlsx]

Requires openpyxl.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

WORKBOOK_VERSION = "2.2.0"
RULES = "A-01 to A-08 (A-02 as amended by B-06), B-02 to B-05, B-07 to B-09"
BENCHMARKS = json.loads((Path(__file__).resolve().parents[1] / "data" / "benchmarks" / "benchmarks.json").read_text())
BENCH_FIRST_ROW = 16  # first data row of each table on the Benchmark Rates tab
MAX_MONTHS = 600
CHANGE_ROWS = 20
MAX_RESETS = 120  # repo-linked estimate: reset dates considered (B-09)
MERGED_ROWS = CHANGE_ROWS + MAX_RESETS
FREQ_TEXT = {1: "Every month", 3: "Every 3 months", 6: "Every 6 months", 12: "Every year"}
FIRST_ROW = 8  # first data row of the Repayment Engine
LAST_ROW = FIRST_ROW + MAX_MONTHS - 1

MODE_KEEP_EMI = "Keep EMI, change tenure"
MODE_KEEP_TENURE = "Keep tenure, change EMI"
MODE_BANK_EMI = "Bank set a new EMI"
MODES = [MODE_KEEP_EMI, MODE_KEEP_TENURE, MODE_BANK_EMI]
SOURCE_BANK = "Bank document (statement, letter or app)"
SOURCE_OWN = "My own records"
SOURCES = [SOURCE_BANK, SOURCE_OWN]

BLUE = PatternFill("solid", fgColor="DDEBF7")
GREY = PatternFill("solid", fgColor="F2F2F2")
HEAD = PatternFill("solid", fgColor="1F4E78")
WHITE_BOLD = Font(bold=True, color="FFFFFF")
TITLE = Font(bold=True, size=16, color="1F4E78")
H2 = Font(bold=True, size=12, color="1F4E78")
BOLD = Font(bold=True)
WRAP = Alignment(wrap_text=True, vertical="top")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
RUPEE = '"₹"#,##,##0'
RUPEE_PAISE = '"₹"#,##,##0.00'
DATE = "dd mmm yyyy"


def name(wb: Workbook, label: str, ref: str) -> None:
    wb.defined_names[label] = DefinedName(label, attr_text=ref)


def welcome(wb: Workbook) -> None:
    ws = wb.active
    ws.title = "Welcome"
    ws.column_dimensions["A"].width = 2
    ws.column_dimensions["B"].width = 110
    lines = [
        ("Home Loan Reality Check", TITLE),
        ("Understand where your EMIs have gone, what you still owe, and how much interest may still lie ahead.", None),
        ("Financial awareness, not financial fear. This tool explains; it does not tell you what to do.", None),
        ("", None),
        ("How to use it", H2),
        ("1.  Go to the Loan Profile tab and fill in the blue cells. Sample data is filled in: replace it with your own loan.", None),
        ("2.  If you have a recent statement, add your outstanding balance with its date. That makes the projection much more accurate.", None),
        ("3.  If your interest rate has changed, list each change in the rate table (oldest first). Bank letters and annual statements usually show these.", None),
        ("4.  Open the Loan Reality Check tab for your results and plain-English explanations.", None),
        ("5.  Check the Validation & Assumptions tab for anything flagged, and to see exactly how each number is calculated.", None),
        ("6.  The Repayment Engine tab shows every month of your loan. You don't need to edit it.", None),
        ("7.  If your loan is linked to the RBI repo rate and you don't know all its past rates, turn on the repo-linked estimate in section 4 of the Loan Profile. "
         "Results that use an estimated rate are labelled Illustrative.", None),
        ("8.  On an MCLR or repo-linked loan, the Benchmark Rates tab shows the published SBI and Bank of Baroda MCLR and the RBI repo rate on any date, "
         "to help you fill in past rates. They are references, not your loan's rate.", None),
        ("", None),
        ("What the labels mean", H2),
        ("Each figure says what kind of figure it is and where it came from.", None),
        ("Actual: a figure from your bank or your own records, not calculated by this tool.", None),
        ("Modelled: calculated from complete inputs using the rules on the Validation & Assumptions tab. It is not your bank's own calculation.", None),
        ("Estimated: calculated, but some information (such as past rate changes) is missing or assumed.", None),
        ("Illustrative: based on public benchmark rates or a hypothetical assumption, not your own loan records.", None),
        ("", None),
        ("Colour key", H2),
        ("Blue cells: your inputs.   Grey cells: calculated, don't edit.", None),
        ("", None),
        ("Important", H2),
        ("This is an educational tool. It is not financial, legal or investment advice, and it is not an official lender statement or foreclosure quotation. "
         "Your lender's figures may differ because of day-count methods, payment dates, fees or rate changes not entered here.", None),
        ("", None),
        (f"Workbook version {WORKBOOK_VERSION}. Calculation rules: {RULES}. "
         "The same rules are used by the Loan Intelligence website.", Font(italic=True, color="7F7F7F")),
    ]
    for i, (text, font) in enumerate(lines, start=1):
        c = ws.cell(row=i, column=2, value=text)
        c.alignment = WRAP
        if font:
            c.font = font


def profile(wb: Workbook) -> None:
    ws = wb.create_sheet("Loan Profile")
    for col, w in zip("ABCDEFG", [2, 46, 20, 30, 18, 34, 60]):
        ws.column_dimensions[col].width = w
    ws["B1"] = "Loan Profile"
    ws["B1"].font = TITLE
    ws["B2"] = "Fill in the blue cells. Grey cells are calculated for you. Sample data is filled in: replace it with your own loan."

    def field(row: int, label: str, value, nm: str, fmt: str | None, hint: str) -> None:
        ws.cell(row=row, column=2, value=label).alignment = WRAP
        c = ws.cell(row=row, column=3, value=value)
        c.fill = BLUE
        c.border = BOX
        if fmt:
            c.number_format = fmt
        ws.cell(row=row, column=4, value=hint).alignment = WRAP
        ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=7)
        name(wb, nm, f"'Loan Profile'!$C${row}")

    ws["B4"] = "1. Your loan when it started"
    ws["B4"].font = H2
    field(5, "Original loan amount (₹)", 5000000, "LoanAmt", RUPEE, "The amount disbursed, from your sanction letter. This version supports fully disbursed loans only.")
    field(6, "Date of your first EMI", dt.date(2020, 4, 5), "FirstEMI", DATE, "The due date of EMI number 1. Later EMIs fall on the same day each month (or the month's last day when that day doesn't exist).")
    field(7, "Original tenure (months)", 240, "Tenure", "0", "For example, 20 years = 240 months.")
    field(8, "Interest rate at the start (% per year)", 8.5, "StartRate", "0.00", "For example 8.5 for 8.5%.")
    field(9, "EMI at the start (₹, optional)", None, "StartEMIIn", RUPEE_PAISE, "Leave blank to let the sheet calculate it. If you enter your bank's EMI, the sheet uses yours.")

    ws["B11"] = "2. Where your loan stands today (optional)"
    ws["B11"].font = H2
    field(12, "Report date (optional)", None, "AsOfIn", DATE, "Leave blank to use today's date.")
    field(13, "Number of EMIs paid so far (optional)", None, "EMIsPaidIn", "0", "Leave blank to count it from your first EMI date. Enter it if you know it from your statement.")
    field(14, "Outstanding principal (₹, optional)", None, "BankOut", RUPEE_PAISE, "From a statement. Needs the date below: an undated balance can't be used.")
    field(15, "Date of that outstanding balance", None, "BankAt", DATE, "The 'as at' date printed on the statement.")
    field(16, "Where that balance comes from", SOURCE_BANK, "BankSource", None, "A bank document, or your own records.")
    field(17, "Document (optional)", None, "BankDoc", None, "For example 'annual statement 2024-25' or 'bank app'.")

    ws["B19"] = "3. Interest rate changes since the loan started"
    ws["B19"].font = H2
    field(20, "Have you entered every rate change?", "Yes", "RateKnown", None, "'Yes' if the rate never changed or every change is listed below. 'No' or 'Not sure' means figures that depend on past rates are Estimated.")
    hdr = ["Effective date", "New rate (% p.a.)", "What your bank did", "New EMI (₹, if the bank set one)", "Where this rate came from"]
    for j, h in enumerate(hdr):
        c = ws.cell(row=22, column=2 + j, value=h)
        c.font = WHITE_BOLD
        c.fill = HEAD
        c.alignment = WRAP
    ws.cell(row=22, column=7, value="List changes oldest first. A change applies from the first EMI period (one EMI date to the next) that starts on or after its date. "
                                   "Leave 'New EMI' blank unless you chose 'Bank set a new EMI'.").alignment = WRAP
    sample = [
        (dt.date(2022, 6, 1), 9.0, MODE_KEEP_EMI, None, SOURCE_BANK),
        (dt.date(2023, 3, 1), 9.25, MODE_KEEP_TENURE, None, SOURCE_BANK),
        (dt.date(2025, 4, 1), 8.75, MODE_KEEP_EMI, None, SOURCE_OWN),
    ]
    r0, r1 = 23, 23 + CHANGE_ROWS - 1
    for i in range(CHANGE_ROWS):
        row = r0 + i
        vals = sample[i] if i < len(sample) else (None,) * 5
        for j, v in enumerate(vals):
            c = ws.cell(row=row, column=2 + j, value=v)
            c.fill = BLUE
            c.border = BOX
            c.number_format = [DATE, "0.00", "@", RUPEE_PAISE, "@"][j]
        # hidden helper: mode code E/T/B
        ws.cell(row=row, column=8, value=f'=IF(D{row}="{MODE_KEEP_TENURE}","T",IF(D{row}="{MODE_BANK_EMI}","B","E"))')
        # hidden helper: sort key (date, then list order) for merging with estimates
        ws.cell(row=row, column=9, value=f'=IF(ISNUMBER(B{row}),B{row}+{i + 1}/1000,"")')
    ws.column_dimensions["H"].hidden = True
    ws.column_dimensions["I"].hidden = True
    name(wb, "EntDates", f"'Loan Profile'!$B${r0}:$B${r1}")
    name(wb, "EntRates", f"'Loan Profile'!$C${r0}:$C${r1}")
    name(wb, "EntModeText", f"'Loan Profile'!$D${r0}:$D${r1}")
    name(wb, "EntEMIs", f"'Loan Profile'!$E${r0}:$E${r1}")
    name(wb, "EntSources", f"'Loan Profile'!$F${r0}:$F${r1}")
    name(wb, "EntModes", f"'Loan Profile'!$H${r0}:$H${r1}")
    name(wb, "EntKeys", f"'Loan Profile'!$I${r0}:$I${r1}")

    q = r1 + 2
    ws.cell(row=q, column=2, value="4. If your loan is linked to the RBI repo rate (optional)").font = H2
    field(q + 1, "Estimate past rates you don't know from the RBI repo rate?", "No", "RepoOn", None,
          "Only for repo-linked loans. At each reset date the sheet uses the RBI repo rate plus your spread, and adds a rate change if the rate moved. "
          "Rate changes you entered above always win. Results that use an estimated rate are labelled Illustrative.")
    field(q + 2, "How often your bank resets the rate", FREQ_TEXT[3], "RepoFreqText", None,
          "From your sanction letter or loan agreement. If you're not sure, leave it at every 3 months.")
    field(q + 3, "First reset date (optional)", None, "RepoFirstIn", DATE,
          "Leave blank to assume the first reset one reset interval after disbursement.")
    field(q + 4, "Your spread over the repo rate (% p.a., optional)", None, "RepoSpreadIn", "0.00",
          "From your sanction letter, e.g. 2.75. Leave blank to work it out from your latest known rate.")
    dv_on = DataValidation(type="list", formula1='"Yes,No"', allow_blank=False)
    dv_freq = DataValidation(type="list", formula1='"' + ",".join(FREQ_TEXT.values()) + '"', allow_blank=False)
    ws.add_data_validation(dv_on)
    ws.add_data_validation(dv_freq)
    dv_on.add(f"C{q + 1}")
    dv_freq.add(f"C{q + 2}")

    dv_mode = DataValidation(type="list", formula1='"' + ",".join(MODES) + '"', allow_blank=True)
    dv_src = DataValidation(type="list", formula1='"' + ",".join(SOURCES) + '"', allow_blank=True)
    dv_known = DataValidation(type="list", formula1='"Yes,No,Not sure"', allow_blank=False)
    for dv in (dv_mode, dv_src, dv_known):
        ws.add_data_validation(dv)
    dv_mode.add(f"D{r0}:D{r1}")
    dv_src.add(f"F{r0}:F{r1}")
    dv_src.add("C16")
    dv_known.add("C20")

    base = q + 6
    ws.cell(row=base, column=2, value="Calculated from your inputs (don't edit)").font = H2
    calc = [
        ("Report date used", "=IF(AsOfIn=\"\",TODAY(),AsOfIn)", "AsOf", DATE),
        ("EMI calculated from the starting loan, rate and tenure",
         "=IF(OR(LoanAmt=\"\",Tenure=\"\",StartRate=\"\"),0,IF(StartRate=0,ROUND(ROUND(LoanAmt/Tenure,6),2),ROUND(ROUND(PMT(StartRate/1200,Tenure,-LoanAmt),6),2)))",
         "ModelEMI", RUPEE_PAISE),
        ("EMI used from EMI number 1", "=IF(StartEMIIn=\"\",ModelEMI,StartEMIIn)", "EMIUsed", RUPEE_PAISE),
        ("Bank balance can be used (has a date)?", "=AND(BankOut<>\"\",ISNUMBER(BankAt))", "BankValid", None),
        ("Source of that balance", f"=IF(BankSource=\"{SOURCE_OWN}\",\"customer-provided\",\"bank-confirmed\")", "BankSrcCode", None),
        ("Disbursement date (one month before EMI 1)", "=EDATE(FirstEMI,-1)", "Disbursed", DATE),
        ("Reset interval (months)", "=IFERROR(CHOOSE(MATCH(RepoFreqText,{" + ",".join(f'"{t}"' for t in FREQ_TEXT.values()) + "},0)," + ",".join(str(m) for m in FREQ_TEXT) + "),3)", "RepoFreq", "0"),
        ("First reset date used", "=IF(ISNUMBER(RepoFirstIn),RepoFirstIn,EDATE(Disbursed,RepoFreq))", "RepoAnchor", DATE),
        ("Rate changes estimated from the repo rate", "=COUNTIF(EstEmit,TRUE)", "EstCount", "0"),
    ]
    for i, (label, formula, nm, fmt) in enumerate(calc, start=1):
        row = base + i
        ws.cell(row=row, column=2, value=label).alignment = WRAP
        c = ws.cell(row=row, column=3, value=formula)
        c.fill = GREY
        if fmt:
            c.number_format = fmt
        name(wb, nm, f"'Loan Profile'!$C${row}")


def engine(wb: Workbook) -> None:
    ws = wb.create_sheet("Repayment Engine")
    ws["A1"] = "Repayment Engine"
    ws["A1"].font = TITLE
    ws["A2"] = ("Every month of your loan under the approved rules. Interest = opening balance × rate ÷ 1200, rounded to the paisa. "
                "A rate change applies from the first period (EMI date to EMI date) starting on or after its date. Don't edit this tab.")
    ws["A3"] = "Amounts are in rupees to the paisa. Rows stop when the loan is repaid (or after 600 months)."
    headers = ["EMI no.", "Live", "Period start", "EMI due date", "Bank balance used here", "Rate changes so far",
               "Rate change here", "Rate (% p.a.)", "Choice", "Opening balance", "Scheduled last EMI no. (0 = moving)",
               "EMI", "Interest", "Payment", "Principal", "Closing balance", "Notes", "Past / future", "Row check (0 = adds up)"]
    widths = [8, 6, 13, 13, 10, 9, 9, 9, 7, 16, 12, 14, 14, 14, 14, 16, 30, 9, 9]
    for j, (h, w) in enumerate(zip(headers, widths), start=1):
        c = ws.cell(row=7, column=j, value=h)
        c.font = WHITE_BOLD
        c.fill = HEAD
        c.alignment = WRAP
        ws.column_dimensions[c.column_letter].width = w
    ws.row_dimensions[7].height = 45
    ws.freeze_panes = "C8"

    for r in range(FIRST_ROW, LAST_ROW + 1):
        p = r - 1
        first = r == FIRST_ROW
        f = {}
        f["A"] = f"={r - FIRST_ROW + 1}"
        f["B"] = "=TRUE" if first else f"=AND(B{p},P{p}>0,A{r}<={MAX_MONTHS})"
        f["C"] = f'=IF(B{r},EDATE(FirstEMI,A{r}-2),"")'
        f["D"] = f'=IF(B{r},EDATE(FirstEMI,A{r}-1),"")'
        f["E"] = (f"=AND(B{r},BankValid,D{r}>BankAt)" if first
                  else f"=AND(B{r},BankValid,D{r}>BankAt,D{p}<=BankAt)")
        f["F"] = f'=IF(B{r},COUNTIF(ChgDates,"<="&C{r}),' + ("0)" if first else f"F{p})")
        f["G"] = f"=AND(B{r},F{r}>0)" if first else f"=AND(B{r},F{r}>F{p})"
        f["H"] = f'=IF(B{r},IF(F{r}=0,StartRate,INDEX(ChgRates,F{r})),"")'
        f["I"] = f'=IF(G{r},INDEX(ChgModes,F{r}),"")'
        prev_bal = "LoanAmt" if first else f"P{p}"
        f["J"] = f'=IF(B{r},IF(E{r},BankOut,{prev_bal}),"")'
        prev_mat = "Tenure" if first else f"K{p}"
        prev_rate = "StartRate" if first else f"H{p}"
        prev_emi = "EMIUsed" if first else f"L{p}"
        clear = (f"IF({prev_rate}=0,ROUNDUP(ROUND(J{r}/{prev_emi},9),0),"
                 f"ROUNDUP(ROUND(NPER({prev_rate}/1200,-{prev_emi},J{r}),9),0))")
        f["K"] = (f'=IF(B{r},IF(G{r},IF(I{r}="E",0,IF(I{r}="T",IF({prev_mat}=0,A{r}-1+IFERROR({clear},NA()),{prev_mat}),{prev_mat})),{prev_mat}),"")')
        recalc = (f"IF(H{r}=0,ROUND(ROUND(J{r}/(K{r}-A{r}+1),6),2),"
                  f"ROUND(ROUND(PMT(H{r}/1200,K{r}-A{r}+1,-J{r}),6),2))")
        f["L"] = (f'=IF(B{r},IF(G{r},IF(I{r}="B",INDEX(ChgEMIs,F{r}),IF(I{r}="T",{recalc},{prev_emi})),{prev_emi}),"")')
        f["M"] = f'=IF(B{r},ROUND(ROUND(J{r}*H{r}/1200,6),2),"")'
        f["N"] = f'=IF(B{r},IF(OR(AND(K{r}>0,A{r}>=K{r}),ROUND(J{r}+M{r},2)<=L{r}),ROUND(J{r}+M{r},2),L{r}),"")'
        f["O"] = f'=IF(B{r},ROUND(N{r}-M{r},2),"")'
        f["P"] = f'=IF(B{r},ROUND(J{r}-O{r},2),"")'
        f["Q"] = (f'=IF(B{r},TRIM(IF(E{r},"bank balance used ","")&IF(G{r},"rate change ","")'
                  f'&IF(AND(A{r}>1,N{r}<>L{r}),"final EMI adjusted ","")&IF(N{r}<=M{r},"EMI does not cover interest","")),"")')
        f["R"] = f'=IF(B{r},IF(A{r}<=EMIsPaid,"Past","Future"),"")'
        f["S"] = f"=IF(B{r},IF(AND(ABS(M{r}+O{r}-N{r})<0.001,ABS(J{r}-O{r}-P{r})<0.001),0,1),0)"
        for col, formula in f.items():
            c = ws[f"{col}{r}"]
            c.value = formula
            if col in "CD":
                c.number_format = DATE
            elif col in "JLMNOP":
                c.number_format = RUPEE_PAISE
            elif col == "H":
                c.number_format = "0.00"
    rng = lambda col: f"'Repayment Engine'!${col}${FIRST_ROW}:${col}${LAST_ROW}"  # noqa: E731
    for nm, col in [("E_N", "A"), ("E_Live", "B"), ("E_Start", "C"), ("E_Due", "D"), ("E_Bank", "E"),
                    ("E_Rate", "H"), ("E_Open", "J"), ("E_EMI", "L"), ("E_Int", "M"), ("E_Pay", "N"),
                    ("E_Prin", "O"), ("E_Close", "P"), ("E_Notes", "Q"), ("E_Check", "S")]:
        name(wb, nm, rng(col))
    ws.conditional_formatting.add(
        f"A{FIRST_ROW}:R{LAST_ROW}",
        FormulaRule(formula=[f'$R{FIRST_ROW}="Past"'], fill=PatternFill("solid", fgColor="EDEDED")),
    )
    ws.conditional_formatting.add(
        f"Q{FIRST_ROW}:Q{LAST_ROW}",
        FormulaRule(formula=[f'ISNUMBER(SEARCH("does not cover",$Q{FIRST_ROW}))'],
                    fill=PatternFill("solid", fgColor="F8CBAD")),
    )


def rate_estimate(wb: Workbook) -> None:
    """Repo-linked estimate (A-05, B-03, B-09) and the merged rate-change list
    the Repayment Engine reads (entered changes plus estimated ones, by date)."""
    ws = wb.create_sheet("Rate Estimate")
    ws["A1"] = "Rate Estimate"
    ws["A1"].font = TITLE
    ws["A2"] = ("Used only when 'Estimate past rates from the RBI repo rate' is Yes on the Loan Profile tab. At each reset date: "
                "estimate = RBI repo rate on that date + spread; spread = your sanction-letter spread, or else your latest known rate "
                "minus the repo rate on that rate's date. No estimate in a reset interval where you entered a rate change, or where "
                "a repo rate is not available. Don't edit this tab.")
    ws["A2"].alignment = WRAP
    ws.merge_cells("A2:N2")
    ws.row_dimensions[2].height = 45
    hdr = ["Reset no.", "Reset date", "Next reset", "In use", "Known changes by then", "Known rate's date", "Known rate",
           "Repo rate", "Spread", "Estimate", "Rate just before", "You entered a change in this interval", "Becomes a rate change",
           "Sort key", "", "Merged: sort key", "Date", "Rate", "Choice", "Bank EMI"]
    for j, h in enumerate(hdr, start=1):
        if h:
            c = ws.cell(row=4, column=j, value=h)
            c.font = WHITE_BOLD
            c.fill = HEAD
            c.alignment = WRAP
    ws.row_dimensions[4].height = 45
    f0 = 5
    for k in range(MAX_RESETS):
        r = f0 + k
        p = r - 1
        ws[f"A{r}"] = k
        ws[f"B{r}"] = f"=EDATE(RepoAnchor,A{r}*RepoFreq)"
        ws[f"C{r}"] = f"=EDATE(RepoAnchor,(A{r}+1)*RepoFreq)"
        ws[f"D{r}"] = f'=AND(RepoOn="Yes",B{r}<=AsOf)'
        ws[f"E{r}"] = f'=COUNTIF(EntDates,"<="&B{r})'
        ws[f"F{r}"] = f"=IF(E{r}=0,Disbursed,INDEX(EntDates,E{r}))"
        ws[f"G{r}"] = f"=IF(E{r}=0,StartRate,INDEX(EntRates,E{r}))"
        ws[f"H{r}"] = f'=IFERROR(INDEX(RepoRates,MATCH(B{r},RepoDates,1)),"")'
        ws[f"I{r}"] = f'=IF(ISNUMBER(RepoSpreadIn),RepoSpreadIn,IFERROR(ROUND(G{r}-INDEX(RepoRates,MATCH(F{r},RepoDates,1)),6),""))'
        ws[f"J{r}"] = f'=IF(OR(H{r}="",I{r}=""),"",IF(ROUND(H{r}+I{r},6)<=0,"",ROUND(H{r}+I{r},6)))'
        ws[f"K{r}"] = f"=G{r}" if k == 0 else f'=IF(OR(F{r}>=B{p},J{p}=""),G{r},J{p})'
        ws[f"L{r}"] = f'=COUNTIFS(EntDates,">="&B{r},EntDates,"<"&C{r})>0'
        ws[f"M{r}"] = f'=AND(D{r},NOT(L{r}),J{r}<>"",IF(J{r}="",FALSE,ROUND(J{r}-K{r},6)<>0))'
        ws[f"N{r}"] = f'=IF(M{r},B{r}+0.5,"")'
        for col in "BCF":
            ws[f"{col}{r}"].number_format = DATE
    last = f0 + MAX_RESETS - 1
    name(wb, "EstEmit", f"'Rate Estimate'!$M${f0}:$M${last}")

    # Candidate list: entered changes then estimates, one contiguous column of keys.
    # Columns V..Z (hidden) hold candidates; P..T hold the merged list sorted by key.
    for i in range(MERGED_ROWS):
        r = f0 + i
        if i < CHANGE_ROWS:
            src = 23 + i
            ws[f"V{r}"] = f"='Loan Profile'!I{src}"
            ws[f"W{r}"] = f"='Loan Profile'!C{src}"
            ws[f"X{r}"] = f"='Loan Profile'!H{src}"
            ws[f"Y{r}"] = f"='Loan Profile'!E{src}"
        else:
            er = f0 + i - CHANGE_ROWS
            ws[f"V{r}"] = f"=N{er}"
            ws[f"W{r}"] = f"=J{er}"
            ws[f"X{r}"] = "E"
            ws[f"Y{r}"] = None
    cand = lambda col: f"$" + col + f"${f0}:$" + col + f"${f0 + MERGED_ROWS - 1}"  # noqa: E731
    for i in range(MERGED_ROWS):
        r = f0 + i
        ws[f"P{r}"] = f'=IFERROR(SMALL({cand("V")},{i + 1}),"")'
        ws[f"Q{r}"] = f'=IF(P{r}="","",INT(P{r}))'
        ws[f"R{r}"] = f'=IF(P{r}="","",INDEX({cand("W")},MATCH(P{r},{cand("V")},0)))'
        ws[f"S{r}"] = f'=IF(P{r}="","",INDEX({cand("X")},MATCH(P{r},{cand("V")},0)))'
        ws[f"T{r}"] = f'=IF(P{r}="","",INDEX({cand("Y")},MATCH(P{r},{cand("V")},0)))'
        ws[f"Q{r}"].number_format = DATE
    for col in "VWXY":
        ws.column_dimensions[col].hidden = True
    mlast = f0 + MERGED_ROWS - 1
    name(wb, "ChgDates", f"'Rate Estimate'!$Q${f0}:$Q${mlast}")
    name(wb, "ChgRates", f"'Rate Estimate'!$R${f0}:$R${mlast}")
    name(wb, "ChgModes", f"'Rate Estimate'!$S${f0}:$S${mlast}")
    name(wb, "ChgEMIs", f"'Rate Estimate'!$T${f0}:$T${mlast}")
    ws.freeze_panes = "B5"


def reality(wb: Workbook) -> None:
    ws = wb.create_sheet("Loan Reality Check", 2)
    for col, w in zip("ABCDE", [2, 40, 20, 30, 80]):
        ws.column_dimensions[col].width = w
    ws["B1"] = "Loan Reality Check"
    ws["B1"].font = TITLE
    ws["B2"] = '=IF(COUNTIF(V_Status,"Error")>0,"Some inputs need fixing: see the Validation & Assumptions tab. Results below may be wrong.","Report date: "&TEXT(AsOf,"dd mmm yyyy"))'

    # Hidden helper block in column H/I
    helpers = [
        ("RowCount", '=COUNTIF(E_Live,TRUE)'),
        ("Closed", "=INDEX(E_Close,RowCount)=0"),
        ("CountedPaid", '=COUNTIFS(E_Due,"<="&AsOf,E_Live,TRUE)'),
        ("EMIsPaid", '=MIN(IF(EMIsPaidIn="",CountedPaid,EMIsPaidIn),RowCount)'),
        ("BankRow", "=IFERROR(MATCH(TRUE,E_Bank,0),0)"),
        ("BankUsed", "=AND(BankValid,BankRow>0,BankAt<=AsOf)"),
        ("BankLatest", "=AND(BankUsed,EMIsPaid<BankRow)"),
        ("BankModelled", "=IF(BankRow=0,\"\",IF(BankRow=1,LoanAmt,INDEX(E_Close,BankRow-1)))"),
        ("HistKind", '=IF(EstCount>0,"Illustrative",IF(RateKnown="Yes","Modelled","Estimated"))'),
        ("PaidKind", '=IF(EMIsPaidIn="","Estimated","Actual")'),
        ("PastKind", '=IF(HistKind="Illustrative","Illustrative",IF(OR(HistKind="Estimated",PaidKind="Estimated"),"Estimated","Modelled"))'),
        ("OutKind", '=IF(BankLatest,"Actual",PastKind)'),
        ("FutKind", '=IF(OR(OutKind="Illustrative",HistKind="Illustrative"),"Illustrative",IF(OR(OutKind="Estimated",HistKind="Estimated"),"Estimated","Modelled"))'),
        ("CalcSource", '=IF(HistKind="Illustrative","from public benchmark rates","calculated")'),
        ("OutSource", '=IF(BankLatest,IF(BankSrcCode="bank-confirmed","from your bank","as you entered it"),CalcSource)'),
    ]
    for i, (nm, formula) in enumerate(helpers, start=4):
        ws.cell(row=i, column=8, value=nm)
        ws.cell(row=i, column=9, value=formula)
        name(wb, nm, f"'Loan Reality Check'!$I${i}")
    ws.column_dimensions["H"].hidden = True
    ws.column_dimensions["I"].hidden = True

    hdr = ["Figure", "Amount", "Type of figure", "How it was worked out"]
    for j, h in enumerate(hdr, start=2):
        c = ws.cell(row=4, column=j, value=h)
        c.font = WHITE_BOLD
        c.fill = HEAD
    paid = "SUMIFS({col},E_N,\"<=\"&EMIsPaid)"
    rows = [
        ("EMIs paid so far", "=EMIsPaid", "0", '=PaidKind&IF(PaidKind="Actual"," · as you entered it"," · calculated")',
         '=IF(EMIsPaidIn="","Counted from your first EMI date to the report date, assuming every EMI was paid on its due date.","The number of EMIs you told us you have paid.")'),
        ("Total EMIs paid", "=" + paid.format(col="E_Pay"), RUPEE, '=PastKind&" · "&CalcSource',
         '="All the EMIs paid so far, added up."'),
        ("Principal repaid", "=" + paid.format(col="E_Prin"), RUPEE, '=PastKind&" · "&CalcSource',
         '="The part of your EMIs that reduced the loan itself."'),
        ("Interest paid", "=" + paid.format(col="E_Int"), RUPEE, '=PastKind&" · "&CalcSource',
         '="The part of your EMIs that went to interest. Early in a loan most of each EMI is interest, because interest is charged on a large balance."'),
        ("Outstanding principal today", "=IF(BankLatest,BankOut,IF(EMIsPaid=0,LoanAmt,INDEX(E_Close,EMIsPaid)))", RUPEE,
         '=OutKind&" · "&OutSource',
         '=IF(BankLatest,"The outstanding balance from your "&IF(BankDoc="","statement",BankDoc)&", dated "&TEXT(BankAt,"dd mmm yyyy")&".",IF(BankUsed,"Worked forward from the balance you gave us, dated "&TEXT(BankAt,"dd mmm yyyy")&", by the EMIs due since then.","What you still owe on the loan itself, after the principal repaid so far."))'),
        ("Interest still to pay (projection)", "=SUM(E_Int)-" + paid.format(col="E_Int"), RUPEE, '=FutKind&" · "&CalcSource',
         '="Interest still to come if your rate and EMI stay as they are. This is a projection, separate from interest already paid."'),
        ("EMIs still to pay", "=IF(Closed,RowCount-EMIsPaid,0)", "0", '=FutKind&" · "&CalcSource',
         '=IF(Closed,"EMIs still to pay before the loan closes.","Your loan does not close at the current EMI and rate. See the Validation tab.")'),
        ("Estimated last EMI date", '=IF(Closed,INDEX(E_Due,RowCount),"Does not close")', DATE, '=FutKind&" · "&CalcSource',
         '="The due date of your last EMI if your rate and EMI stay as they are."'),
        ("Current EMI", "=INDEX(E_EMI,MAX(1,MIN(RowCount,EMIsPaid+1)))", RUPEE, '=IF(StartEMIIn="","Modelled · calculated","Actual · as you entered it")',
         '="The EMI the sheet uses for your next payment."'),
    ]
    for i, (label, value, fmt, kind, expl) in enumerate(rows, start=5):
        ws.cell(row=i, column=2, value=label).font = BOLD
        c = ws.cell(row=i, column=3, value=value)
        c.number_format = fmt
        c.fill = GREY
        ws.cell(row=i, column=4, value=kind)
        ws.cell(row=i, column=5, value=expl).alignment = WRAP

    r = 5 + len(rows) + 1
    ws.cell(row=r, column=2, value="Your bank's balance compared with this sheet").font = H2
    cmp_rows = [
        ("Bank's outstanding", '=IF(BankRow>0,BankOut,"Not entered")', RUPEE),
        ("This sheet's model on that date", '=IF(BankRow>0,BankModelled,"")', RUPEE),
        ("Difference (bank minus model)", '=IF(BankRow>0,BankOut-BankModelled,"")', RUPEE),
        ("What this means", '=IF(BankRow=0,"Add a dated balance from a statement on the Loan Profile tab to compare.",'
                             'IF(ABS(BankOut-BankModelled)<1,"Your bank and this sheet agree.",'
                             '"Both figures are kept. The sheet never changes your history to match the bank. Common reasons for a difference: a rate change not entered, '
                             'different payment dates, a missed or extra payment, fees, or the bank using a daily interest method. From that date on, projections start from the bank figure."))', None),
    ]
    for i, (label, formula, fmt) in enumerate(cmp_rows, start=r + 1):
        ws.cell(row=i, column=2, value=label)
        c = ws.cell(row=i, column=3, value=formula)
        if fmt:
            c.number_format = fmt
        if label == "What this means":
            ws.merge_cells(start_row=i, start_column=3, end_row=i, end_column=5)
            c.alignment = WRAP
            ws.row_dimensions[i].height = 45

    r2 = r + len(cmp_rows) + 2
    ws.cell(row=r2, column=2, value="Explanations").font = H2
    notes = [
        "Why was so much of my EMI interest at first? Interest is charged each month on what you still owe. At the start you owe the most, so most of the EMI goes to interest and only a little reduces the loan.",
        "Why is my outstanding still high? Because principal repayment starts small and grows each month. In a 20-year loan, the balance usually falls slowly for the first half and faster later.",
        "How do rate changes affect me? A higher rate means more of each EMI goes to interest. If your bank keeps the EMI the same, your loan takes longer to repay; if it keeps the tenure, your EMI rises.",
        "Amounts are calculated to the paisa and shown to the nearest rupee, so a column of figures may differ from its total by a rupee.",
    ]
    for i, t in enumerate(notes, start=r2 + 1):
        c = ws.cell(row=i, column=2, value=t)
        ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=5)
        c.alignment = WRAP
        ws.row_dimensions[i].height = 32

    chart = LineChart()
    chart.title = "Outstanding balance after each EMI"
    chart.y_axis.title = "₹"
    chart.x_axis.title = "EMI number"
    eng = wb["Repayment Engine"]
    chart.add_data(Reference(eng, min_col=16, min_row=7, max_row=LAST_ROW), titles_from_data=True)
    chart.height = 8
    chart.width = 22
    ws.add_chart(chart, f"B{r2 + len(notes) + 2}")


def validation(wb: Workbook) -> None:
    ws = wb.create_sheet("Validation & Assumptions")
    for col, w in zip("ABCD", [2, 60, 10, 90]):
        ws.column_dimensions[col].width = w
    ws["B1"] = "Validation & Assumptions"
    ws["B1"].font = TITLE
    ws["B2"] = "Status: OK = fine. Check = worth a look, numbers still work. Error = fix this input; results may be wrong."
    ws["B4"] = "Input checks"
    ws["B4"].font = H2
    for j, h in enumerate(["Check", "Status", "Detail"], start=2):
        c = ws.cell(row=5, column=j, value=h)
        c.font = WHITE_BOLD
        c.fill = HEAD
    chg_pairs_bad = 'SUMPRODUCT((EntDates<>"")*(EntRates=""))+SUMPRODUCT((EntDates="")*(EntRates<>""))'
    order_bad = (f"SUMPRODUCT(('Loan Profile'!$B$24:$B${23 + CHANGE_ROWS - 1}<>\"\")*"
                 f"('Loan Profile'!$B$24:$B${23 + CHANGE_ROWS - 1}<='Loan Profile'!$B$23:$B${23 + CHANGE_ROWS - 2}))")
    checks = [
        ("Loan amount is filled in and positive",
         '=IF(AND(ISNUMBER(LoanAmt),LoanAmt>0),IF(LoanAmt>200000000,"Check","OK"),"Error")',
         '=IF(C6="Error","Enter your original loan amount in rupees.",IF(C6="Check","Loan above ₹20 crore: please double-check the amount.",""))'),
        ("First EMI date is a valid date", '=IF(ISNUMBER(FirstEMI),"OK","Error")',
         '=IF(C7="OK","","Enter the due date of your first EMI.")'),
        ("Tenure is between 1 and 480 months",
         '=IF(AND(ISNUMBER(Tenure),Tenure>=1,Tenure<=480,Tenure=INT(Tenure)),"OK","Error")',
         '=IF(C8="OK","","Enter the original tenure in whole months, between 1 and 480 (40 years).")'),
        ("Starting interest rate looks sensible",
         '=IF(NOT(ISNUMBER(StartRate)),"Error",IF(OR(StartRate<0,StartRate>25),"Error",IF(AND(StartRate>0,OR(StartRate<5,StartRate>15)),"Check","OK")))',
         '=IF(C9="OK","",IF(C9="Error","Enter the rate as a percentage between 0 and 25, for example 8.5.","Rates outside 5% to 15% are unusual for Indian home loans. Did you enter 0.085 instead of 8.5?"))'),
        ("Your starting EMI matches the calculated EMI",
         '=IF(StartEMIIn="","OK",IF(ABS(StartEMIIn-ModelEMI)<=MAX(2,ModelEMI*0.01),"OK","Check"))',
         '=IF(StartEMIIn="","Not entered: using the calculated EMI of ₹"&TEXT(ModelEMI,"#,##0.00")&".",IF(C10="OK","","Your EMI (₹"&TEXT(StartEMIIn,"#,##0")&") differs from the calculated ₹"&TEXT(ModelEMI,"#,##0")&". Check the loan amount, rate and tenure."))'),
        ("Outstanding balance has a date",
         '=IF(BankOut="","OK",IF(ISNUMBER(BankAt),"OK","Error"))',
         '=IF(C11="Error","You entered an outstanding balance without its date. It is not used until you add the date from your statement.","")'),
        ("Outstanding balance is between 0 and the original loan",
         '=IF(BankOut="","OK",IF(BankOut<0,"Error",IF(BankOut>LoanAmt,"Check","OK")))',
         '=IF(C12="OK","",IF(C12="Error","The outstanding balance must be zero or more.","Your outstanding balance is above your original loan amount. Please double-check it."))'),
        ("Rate changes: each row has a date and a rate, oldest first, no duplicates",
         f'=IF(({chg_pairs_bad})+({order_bad})>0,"Error",IF(OR(MAX(EntRates)>25,COUNTIF(EntRates,"<0")>0),"Error","OK"))',
         '=IF(C13="OK","","Each rate change needs a date and a rate (0 to 25), listed oldest first, with no two on the same date.")'),
        ("Rate changes: 'Bank set a new EMI' has the EMI filled in",
         f'=IF(SUMPRODUCT((EntModeText="{MODE_BANK_EMI}")*(EntEMIs=""))>0,"Error","OK")',
         '=IF(C14="OK","","You chose \'Bank set a new EMI\' for a change: enter that EMI.")'),
        ("Rate changes: none dated before the loan started",
         '=IF(COUNTIF(EntDates,"<"&FirstEMI)>0,"Check","OK")',
         '=IF(C15="OK","","A rate change is dated before your first EMI. If it was your starting rate, enter it as the starting rate instead.")'),
        ("Rate history complete", '=IF(RateKnown="Yes","OK","Check")',
         '=IF(C16="OK","","Some past rate changes may be missing, so figures that depend on them are Estimated. Add your rate changes from bank letters or statements for better accuracy.")'),
        ("No month where the EMI fails to cover interest", '=IF(COUNTIF(E_Notes,"*does not cover*")=0,"OK","Error")',
         '=IF(C17="OK","","In "&COUNTIF(E_Notes,"*does not cover*")&" month(s) the EMI is no more than the interest, so the balance does not fall. Usually a rate rise with the EMI kept the same: in reality your bank would raise the EMI. Add the EMI change in the rate table.")'),
        ("Loan closes within 50 years", '=IF(Closed,"OK","Error")',
         '=IF(C18="OK","","The loan does not close within 600 EMIs at the current EMI and rate. Check the EMI and rate.")'),
        ("EMIs paid is not more than the loan's EMIs",
         '=IF(EMIsPaidIn="","OK",IF(OR(EMIsPaidIn<0,EMIsPaidIn<>INT(EMIsPaidIn)),"Error",IF(EMIsPaidIn<>CountedPaid,"Check","OK")))',
         '=IF(C19="OK","",IF(C19="Error","EMIs paid must be a whole number, 0 or more.","You entered "&EMIsPaidIn&" EMIs paid; from your dates we count "&CountedPaid&". We\'ve used your number."))'),
        ("Engine check: every row adds up",
         '=IF(SUM(E_Check)=0,"OK","Error")',
         '=IF(C20="OK","","Internal check failed. Please report this.")'),
    ]
    for i, (label, status, detail) in enumerate(checks, start=6):
        ws.cell(row=i, column=2, value=label).alignment = WRAP
        ws.cell(row=i, column=3, value=status)
        ws.cell(row=i, column=4, value=detail).alignment = WRAP
    last = 5 + len(checks)
    name(wb, "V_Status", f"'Validation & Assumptions'!$C$6:$C${last}")
    ws.conditional_formatting.add(f"C6:C{last}", FormulaRule(formula=['C6="Error"'], fill=PatternFill("solid", fgColor="F8CBAD")))
    ws.conditional_formatting.add(f"C6:C{last}", FormulaRule(formula=['C6="Check"'], fill=PatternFill("solid", fgColor="FFE699")))

    a = last + 2
    ws.cell(row=a, column=2, value="How the numbers are calculated (approved rules)").font = H2
    rules = [
        ("A-01", "Interest is charged monthly on the reducing balance: opening balance × annual rate ÷ 1200 (that is, ÷ 12 for the month, ÷ 100 for the percentage)."),
        ("A-02", "Every amount (EMI, interest, principal, balance) is rounded to the paisa, half up. Results are shown to the nearest rupee. The EMI = P × r × (1+r)^n ÷ ((1+r)^n − 1)."),
        ("A-03", "A calculation period runs from one EMI date to the next. A rate change applies from the first period that starts on or after its effective date, for the whole period. No part-month split. If several changes fall inside one period, only the last applies."),
        ("A-04", "For each rate change you choose: keep the EMI and let the tenure move (the default), keep the tenure and recalculate the EMI, or use the EMI your bank set. If you keep the tenure after it has been moving, the end date is the month the loan would have closed at the previous rate and EMI."),
        ("A-05", "If past rates are unknown, the last rate you gave continues until the next change, and results are labelled Estimated. For a repo-linked loan you can instead estimate them from the RBI repo rate plus your spread at each reset date (Loan Profile section 4, Rate Estimate tab); results then are labelled Illustrative. For MCLR loans, enter each past rate; the Benchmark Rates tab shows SBI and Bank of Baroda MCLR as a reference."),
        ("A-06", "A dated outstanding balance from a statement is taken as your balance after every EMI due on or before its date, and becomes the starting point for the next EMI. Your earlier history is never changed to match the bank; the difference is shown on the Loan Reality Check tab."),
        ("A-07", "The final EMI is exactly what remains due (balance plus that month's interest). If the loan has a scheduled end, any small remainder (for example from a rounded bank EMI) is added to the last EMI instead of creating an extra one."),
        ("A-08", "Only fully disbursed loans are supported. The full amount is assumed disbursed one calendar month before EMI 1. Pre-EMI interest and part disbursements are not modelled."),
        ("Dates", "EMIs due on the 29th, 30th or 31st fall on the last day of shorter months and return to the usual day when it exists. Each EMI is assumed paid in full on its due date."),
        ("Not included", "Prepayments, fees, insurance, foreclosure charges, tax benefits (Section 24(b), 80C) and PMAY subsidy are not included in this version."),
        ("Important", "This is an educational tool, not financial advice and not an official lender statement or foreclosure quotation. Always confirm with your lender before acting."),
    ]
    for i, (rid, text) in enumerate(rules, start=a + 1):
        ws.cell(row=i, column=2, value=text).alignment = WRAP
        ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=4)
        ws.cell(row=i, column=1, value=rid)
        ws.row_dimensions[i].height = 32
    ws.column_dimensions["A"].width = 12


def benchmark_series() -> list[tuple[str, dict, str]]:
    """(display name, series, short id) for every bundled benchmark series."""
    out = []
    for kind, label in (("mclr", "MCLR"), ("repo", "repo rate")):
        for s in BENCHMARKS[kind]["series"]:
            title = f"{s['name']} {label}" if kind == "mclr" else "RBI repo rate"
            out.append((title, s, s["id"]))
    return out


TENOR_TEXT = {
    "overnight": "Overnight", "one_month": "1 month", "three_month": "3 months", "six_month": "6 months",
    "one_year": "1 year", "two_year": "2 years", "three_year": "3 years", "five_year": "5 years",
    "repo_rate": "Repo rate",
}


def benchmarks(wb: Workbook) -> None:
    """Published benchmark rates (B-03, B-07): a reference, never the loan's rate."""
    from openpyxl.utils import get_column_letter as col

    ws = wb.create_sheet("Benchmark Rates")
    ws.column_dimensions["A"].width = 2
    ws["B1"] = "Benchmark Rates"
    ws["B1"].font = TITLE
    ws["B2"] = ("Published rates, copied without change from SBI, Bank of Baroda and the RBI. They are a reference to help you "
                "fill in your past rates. They are not your loan's rate: your rate is the benchmark plus your spread, and it "
                "changes on your loan's reset dates. Label: Illustrative, from public benchmark rates.")
    ws["B2"].alignment = WRAP
    ws.merge_cells("B2:J2")
    ws.row_dimensions[2].height = 48

    series = benchmark_series()
    names = [t for t, _, _ in series]
    ws["B4"] = "Look up a rate"
    ws["B4"].font = H2
    ws["B5"], ws["B6"], ws["B7"] = "Benchmark", "Tenor", "On date"
    ws["C5"], ws["C6"], ws["C7"] = names[0], TENOR_TEXT["one_year"], dt.date(2022, 6, 15)
    for r in (5, 6, 7):
        ws[f"B{r}"].font = BOLD
        ws[f"C{r}"].fill = BLUE
        ws[f"C{r}"].border = BOX
    ws["C7"].number_format = DATE
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 30
    dv_b = DataValidation(type="list", formula1='"' + ",".join(names) + '"', allow_blank=False)
    dv_t = DataValidation(type="list", formula1='"' + ",".join(TENOR_TEXT.values()) + '"', allow_blank=False)
    ws.add_data_validation(dv_b)
    ws.add_data_validation(dv_t)
    dv_b.add("C5")
    dv_t.add("C6")

    # Each series is a block of columns: date, then one column per tenor.
    # Row 14 holds the series name, row 15 the tenor names, data from row 16.
    blocks = []
    start = 2
    for title, s, _ in series:
        width = 1 + len(s["tenors"])
        ws.cell(row=13, column=start, value=title).font = H2
        ws.cell(row=14, column=start, value=f"Source: {s['source_url']} (retrieved {s['retrieved']})").font = Font(italic=True, color="7F7F7F")
        for j, h in enumerate(["Effective"] + [TENOR_TEXT[t] for t in s["tenors"]]):
            c = ws.cell(row=15, column=start + j, value=h)
            c.font = WHITE_BOLD
            c.fill = HEAD
        for i, row in enumerate(s["rows"]):
            r = BENCH_FIRST_ROW + i
            ws.cell(row=r, column=start, value=dt.date.fromisoformat(row["effective"])).number_format = DATE
            for j, t in enumerate(s["tenors"], start=1):
                v = row["rates"].get(t)
                ws.cell(row=r, column=start + j, value=float(v) if v is not None else None).number_format = "0.00"
        last = BENCH_FIRST_ROW + len(s["rows"]) - 1
        first_c, last_c = col(start), col(start + width - 1)
        if s["id"] == "rbi_repo":
            name(wb, "RepoDates", f"'Benchmark Rates'!${first_c}${BENCH_FIRST_ROW}:${first_c}${last}")
            name(wb, "RepoRates", f"'Benchmark Rates'!${col(start + 1)}${BENCH_FIRST_ROW}:${col(start + 1)}${last}")
        blocks.append((title, f"${first_c}${BENCH_FIRST_ROW}:${first_c}${last}",
                       f"${col(start + 1)}$15:${last_c}$15", f"${col(start + 1)}${BENCH_FIRST_ROW}:${last_c}${last}"))
        for j in range(width):
            ws.column_dimensions[col(start + j)].width = max(ws.column_dimensions[col(start + j)].width or 0, 11)
        start += width + 1

    # Lookup: pick the block by name, the row by the last effective date on or
    # before the date, and the column by tenor name.
    def pick(part: int) -> str:
        return "CHOOSE(MATCH($C$5,{" + ",".join(f'"{b[0]}"' for b in blocks) + "},0)," + ",".join(b[part] for b in blocks) + ")"

    ws["B9"], ws["B10"], ws["B11"] = "Rate", "Effective from", "Label"
    for r in (9, 10, 11):
        ws[f"B{r}"].font = BOLD
        ws[f"C{r}"].fill = GREY
    row_idx = f"MATCH($C$7,{pick(1)},1)"
    col_idx = f"MATCH($C$6,{pick(2)},0)"
    ws["C9"] = (f'=IFERROR(IF(INDEX({pick(3)},{row_idx},{col_idx})="","Not published for this tenor",'
                f'INDEX({pick(3)},{row_idx},{col_idx})),"No published rate for that date and tenor")')
    ws["C9"].number_format = '0.00"%"'
    ws["C10"] = f'=IFERROR(INDEX({pick(1)},{row_idx}),"")'
    ws["C10"].number_format = DATE
    ws["C11"] = "Illustrative · from public benchmark rates"
    ws["D9"] = "A reference only: not your loan's rate."
    ws["D9"].font = Font(italic=True, color="7F7F7F")
    ws.freeze_panes = "A16"


def build() -> Workbook:
    wb = Workbook()
    welcome(wb)
    profile(wb)
    engine(wb)
    reality(wb)
    validation(wb)
    rate_estimate(wb)
    benchmarks(wb)
    wb.calculation.fullCalcOnLoad = True
    return wb


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "dist" / f"Home_Loan_Reality_Check_v{WORKBOOK_VERSION.split('.')[0]}.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    build().save(out)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
