import pandas as pd


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


def get_latest_quarters(
    raw,
    number_of_quarters=8
):

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

    df = df.tail(
        number_of_quarters
    ).reset_index(
        drop=True
    )

    df["revenue_millions"] = (
        df["revenue"] / 1_000_000
    )

    return df