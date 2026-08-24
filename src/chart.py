import matplotlib.pyplot as plt


def create_revenue_chart(
    df,
    company_name
):

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

    filename = (
        "latest_8_quarters_revenue.png"
    )

    plt.savefig(
        filename,
        dpi=180
    )

    plt.show()

    return filename