from src.sec_api import (
    get_company_cik,
    get_company_facts
)

from src.revenue import (
    find_revenue_tag,
    build_raw_dataframe,
    get_latest_quarters
)

from src.chart import (
    create_revenue_chart
)


def main():

    # Ask user for company
    company_input = input(
        "\nEnter company name or ticker: "
    )

    # Find CIK
    cik = get_company_cik(
        company_input
    )

    print(
        f"\nCIK found: {cik}"
    )

    # Get SEC facts
    facts = get_company_facts(
        cik
    )

    # Get official company name
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

    # Display results
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

    # Create chart
    create_revenue_chart(
        df,
        company_name
    )


if __name__ == "__main__":
    main()