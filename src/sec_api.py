import requests


HEADERS = {
    "User-Agent": "RevenueResearch/1.0 roy.n.landicho@gmail.com"
}


def get_company_list():

    url = "https://www.sec.gov/files/company_tickers.json"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def get_company_cik(company_input):

    companies = get_company_list()

    company_input = (
        company_input
        .lower()
        .strip()
    )

    # Exact ticker match
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

    # Exact company name match
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

    # Partial company name match
    matches = []

    for company in companies.values():

        name = (
            company["title"]
            .lower()
            .strip()
        )

        if company_input in name:

            matches.append(company)

    if not matches:

        raise RuntimeError(
            f"Company '{company_input}' "
            "was not found in SEC."
        )

    if len(matches) == 1:

        return str(
            matches[0]["cik_str"]
        ).zfill(10)

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