import requests
import pandas as pd
import matplotlib.pyplot as plt


# ==========================================
# 1. SEC HEADERS
# ==========================================

HEADERS = {
    "User-Agent": "RevenueResearch/1.0 roy.n.landicho@gmail.com"
}


# ==========================================
# 2. GET COMPANY LIST FROM SEC
# ==========================================

def get_company_list():

    url = "https://www.sec.gov/files/company_tickers.json"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ==========================================
# 3. FIND COMPANY CIK
# ==========================================

def get_company_cik(company_input):

    companies = get_company_list()

    company_input = (
        company_input
        .lower()
        .strip()
    )

    # ======================================
    # First: exact ticker match
    # ======================================

    for company in companies.values():

        ticker = (
            company["ticker"]
            .lower()
            .strip()
        )

        if company_input == ticker:
            return str(
                company["cik_str"]
            ).zfill(10)


    # ======================================
    # Second: exact company name match
    # ======================================

    for company in companies.values():

        name = (
            company["title"]
            .lower()
            .strip()
        )

        if company_input == name:
            return str(
                company["cik_str"]
            ).zfill(10)


    # ======================================
    # Third: partial company name match
    # ======================================

    matches = []

    for company in companies.values():

        name = (
            company["title"]
            .lower()
            .strip()
        )

        if company_input in name:

            matches.append(company)


    # ======================================
    # No match
    # ======================================

    if not matches:

        raise RuntimeError(
            f"Company '{company_input}' "
            "was not found in SEC."
        )


    # ======================================
    # One match
    # ======================================

    if len(matches) == 1:

        return str(
            matches[0]["cik_str"]
        ).zfill(10)


    # ======================================
    # Multiple matches
    # ======================================

    print(
        "\nMultiple companies found:"
    )

    for index, company in enumerate(
        matches,
        start=1
    ):

        print(
            f"{index}. "
            f"{company['title']} "
            f"({company['ticker']})"
        )


    choice = int(
        input("\nSelect company number: ")
    )

    selected = matches[
        choice - 1
    ]

    return str(
        selected["cik_str"]
    ).zfill(10)


# ==========================================
# 4. GET SEC COMPANY FACTS
# ==========================================

def get_company_facts(cik):

    url = (
        f"https://data.sec.gov/api/xbrl/companyfacts/"
        f"CIK{cik}.json"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ==========================================
# 5. FIND REVENUE TAG
# ==========================================

def find_revenue_tag(facts):

    possible_tags = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ]

    for tag in possible_tags:

        if tag in facts["facts"]["us-gaap"]:
            return tag

    raise RuntimeError(
        "Could not find a revenue tag."
    )


# ==========================================
# 6. BUILD RAW DATAFRAME
# ==========================================

def build_raw_dataframe(facts, revenue_tag):

    units = (
        facts["facts"]["us-gaap"]
        [revenue_tag]["units"]
    )

    if "USD" not in units:
        raise RuntimeError(
            "USD revenue facts were not found."
        )

    rows = []

    for item in units["USD"]:

        if item.get("form") not in {
            "10-Q",
            "10-K"
        }:
            continue

        if (
            not item.get("start")
            or not item.get("end")
        ):
            continue

        rows.append({
            "filed": item.get("filed"),
            "form": item.get("form"),
            "fy": item.get("fy"),
            "fp": item.get("fp"),
            "start": item["start"],
            "end": item["end"],
            "value": item["val"],
            "accn": item.get("accn"),
        })

    raw = pd.DataFrame(rows)

    raw["start"] = pd.to_datetime(
        raw["start"]
    )

    raw["end"] = pd.to_datetime(
        raw["end"]
    )

    raw["filed"] = pd.to_datetime(
        raw["filed"]
    )

    raw["days"] = (
        raw["end"] - raw["start"]
    ).dt.days

    return raw


# ==========================================
# 7. GET STANDALONE QUARTER
# ==========================================

def get_quarter(raw, fy, quarter):

    x = raw[
        (raw["fy"] == fy) &
        (raw["fp"] == quarter) &
        (raw["form"] == "10-Q")
    ].copy()

    x = x[
        x["days"].between(80, 100)
    ]

    if x.empty:
        return None

    x = x.sort_values("filed")

    return x.iloc[-1]["value"]


# ==========================================
# 8. GET NINE-MONTH YTD
# ==========================================

def get_nine_month_ytd(raw, fy):

    x = raw[
        (raw["fy"] == fy) &
        (raw["fp"] == "Q3") &
        (raw["form"] == "10-Q")
    ].copy()

    x = x[
        x["days"].between(250, 290)
    ]

    if x.empty:
        return None

    x = x.sort_values("filed")

    return x.iloc[-1]["value"]


# ==========================================
# 9. GET ANNUAL REVENUE
# ==========================================

def get_annual(raw, fy):

    x = raw[
        (raw["fy"] == fy) &
        (raw["fp"] == "FY") &
        (raw["form"] == "10-K")
    ].copy()

    x = x[
        x["days"].between(330, 400)
    ]

    if x.empty:
        return None

    x = x.sort_values("filed")

    return x.iloc[-1]["value"]


# ==========================================
# 10. BUILD QUARTERLY DATA
# ==========================================

def get_latest_quarters(raw, number_of_quarters=8):

    quarterly = []

    fiscal_years = (
        raw["fy"]
        .dropna()
        .unique()
    )

    fiscal_years = sorted(
        fiscal_years.astype(int)
    )

    for fy in fiscal_years:

        # Q1-Q3
        for quarter in [
            "Q1",
            "Q2",
            "Q3"
        ]:

            value = get_quarter(
                raw,
                fy,
                quarter
            )

            if value is None:
                continue

            quarterly.append({
                "quarter": f"FY{fy} {quarter}",
                "fy": fy,
                "fp": quarter,
                "revenue": value
            })

        # Q4
        annual = get_annual(
            raw,
            fy
        )

        nine_month = get_nine_month_ytd(
            raw,
            fy
        )

        if (
            annual is not None
            and nine_month is not None
        ):

            q4 = annual - nine_month

            quarterly.append({
                "quarter": f"FY{fy} Q4",
                "fy": fy,
                "fp": "Q4",
                "revenue": q4
            })

    df = pd.DataFrame(
        quarterly
    )

    if df.empty:
        raise RuntimeError(
            "No quarterly revenue data found."
        )

    # Correct quarter ordering
    quarter_order = {
        "Q1": 1,
        "Q2": 2,
        "Q3": 3,
        "Q4": 4
    }

    df["quarter_order"] = (
        df["fp"].map(quarter_order)
    )

    df = df.sort_values(
        [
            "fy",
            "quarter_order"
        ]
    )

    # Latest N quarters
    df = df.tail(
        number_of_quarters
    ).reset_index(
        drop=True
    )

    # USD → millions
    df["revenue_millions"] = (
        df["revenue"] / 1_000_000
    )

    return df


# ==========================================
# 11. MAIN PROGRAM
# ==========================================

company_input = input(
    "\nEnter company name or ticker: "
)


# Find CIK automatically
cik = get_company_cik(
    company_input
)

print(
    f"\nCIK found: {cik}"
)


# Get company facts
facts = get_company_facts(
    cik
)


# Get official SEC company name
company_name = facts.get(
    "entityName",
    company_input
)

print(
    f"Company: {company_name}"
)


# Find revenue tag
revenue_tag = find_revenue_tag(
    facts
)

print(
    f"Revenue tag: {revenue_tag}"
)


# Build raw dataframe
raw = build_raw_dataframe(
    facts,
    revenue_tag
)


# Get latest 8 quarters
df = get_latest_quarters(
    raw,
    number_of_quarters=8
)


# ==========================================
# 12. DISPLAY RESULT
# ==========================================

print(
    "\nFinal revenue data:"
)

print(
    df[
        [
            "quarter",
            "revenue_millions"
        ]
    ].to_string(
        index=False
    )
)


# ==========================================
# 13. CREATE CHART
# ==========================================

plt.figure(
    figsize=(10, 5.5)
)

plt.plot(
    df["quarter"],
    df["revenue_millions"],
    marker="o"
)

plt.title(
    f"{company_name} Quarterly Revenue "
    f"— Last {len(df)} Fiscal Quarters"
)

plt.xlabel(
    "Fiscal quarter"
)

plt.ylabel(
    "Revenue (USD millions)"
)

plt.xticks(
    rotation=35,
    ha="right"
)

plt.grid(
    True,
    alpha=0.3
)

plt.tight_layout()


# ==========================================
# 14. SAVE CHART
# ==========================================

plt.savefig(
    "latest_8_quarters_revenue.png",
    dpi=180
)

plt.show()