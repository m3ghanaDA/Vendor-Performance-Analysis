import pandas as pd

def get_top_vendors(df):

    return (
        df.groupby("VendorName")
        ["TotalSalesDollars"]
        .sum()
        .reset_index()
        .sort_values(
            "TotalSalesDollars",
            ascending=False
        )
        .head(10)
    )


def get_top_brands(df):

    return (
        df.groupby("Description")
        ["TotalSalesDollars"]
        .sum()
        .reset_index()
        .sort_values(
            "TotalSalesDollars",
            ascending=False
        )
        .head(10)
    )


def get_purchase_contribution(df):

    vendor_purchase = (
        df.groupby("VendorName")
        ["TotalPurchaseDollars"]
        .sum()
        .reset_index()
        .sort_values(
            "TotalPurchaseDollars",
            ascending=False
        )
        .head(10)
    )

    return vendor_purchase


def get_low_performing_vendors(df):

    return (
        df.groupby("VendorName")
        ["StockTurnover"]
        .mean()
        .reset_index()
        .sort_values(
            "StockTurnover"
        )
        .head(10)
    )

def get_promotion_opportunities(df):

    brand_performance = (
        df.groupby("Description")
        .agg({
            "TotalSalesDollars":"sum",
            "ProfitMargin":"mean"
        })
        .reset_index()
    )

    low_sales_threshold = (
        brand_performance[
            "TotalSalesDollars"
        ].quantile(0.15)
    )

    high_margin_threshold = (
        brand_performance[
            "ProfitMargin"
        ].quantile(0.85)
    )

    return brand_performance[
        (
            brand_performance[
                "TotalSalesDollars"
            ]
            <= low_sales_threshold
        )
        &
        (
            brand_performance[
                "ProfitMargin"
            ]
            >= high_margin_threshold
        )
    ]