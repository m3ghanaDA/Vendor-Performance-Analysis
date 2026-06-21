import streamlit as st
import pandas as pd
import plotly.express as px



from utils.analytics import (
    get_top_vendors,
    get_top_brands,
    get_purchase_contribution,
    get_low_performing_vendors,
    get_promotion_opportunities
)

st.set_page_config(
    page_title="Vendor Performance Dashboard",
    layout="wide"
)

st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    padding: 15px;
    border-radius: 10px;
}

div[data-testid="metric-container"] label {
    color: white;
}

div[data-testid="metric-container"] div {
    color: white;
}
</style>
""", unsafe_allow_html=True)





# ==========================
# LOAD DATA
# ==========================

@st.cache_data
def load_data():

    return pd.read_csv(
        "data/vendor_sales_summary.csv"
    )

df = load_data()




# ==========================
# TITLE
# ==========================

st.title("📊 Vendor Performance Dashboard")

st.markdown(
"""
Business Intelligence Dashboard for Vendor Sales,
Inventory and Profitability Analysis.
"""
)

st.divider()




# ==========================
# KPI CARDS
# ==========================

sales = df["TotalSalesDollars"].sum()

purchase = df["TotalPurchaseDollars"].sum()

profit = df["GrossProfit"].sum()

inventory = df["UnsoldInventoryValue"].sum()

margin = (
    profit /
    purchase
) * 100

c1,c2,c3,c4,c5 = st.columns(5)

c1.metric(
    "Sales",
    f"${sales/1e6:.2f}M"
)

c2.metric(
    "Purchases",
    f"${purchase/1e6:.2f}M"
)

c3.metric(
    "Gross Profit",
    f"${profit/1e6:.2f}M"
)

c4.metric(
    "Profit Margin",
    f"{margin:.1f}%"
)

c5.metric(
    "Unsold Capital",
    f"${inventory/1e6:.2f}M"
)

st.divider()
# =====================================================
# ROW 1
# =====================================================

col1, col2 = st.columns(2)

with col1:

    purchase_contribution = get_purchase_contribution(df)

    st.subheader(
    "Purchase Contribution %"
)
    fig1 = px.pie(
        purchase_contribution,
        values="TotalPurchaseDollars",
        names="VendorName",
        hole=0.6,
        
    )

    color_discrete_sequence=px.colors.qualitative.Set2
    
    st.plotly_chart(
        fig1,
        use_container_width=True
    )

with col2:

    top_vendors = get_top_vendors(df)

    st.subheader(
    "Top Vendors by Sales"
)
    fig2 = px.bar(
        top_vendors,
        x="TotalSalesDollars",
        y="VendorName",
        orientation="h"
        
    )
   
    fig2.update_traces(
    marker_color="#00B0F0"
    )

    fig2.update_layout(
        yaxis={
            "categoryorder":
            "total ascending"
        }
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )




# =====================================================
# ROW 2
# =====================================================

col3, col4 = st.columns(2)

with col3:

    top_brands = get_top_brands(df)
    st.subheader(
    "Top Brands by Sales"
)
    fig3 = px.bar(
        top_brands,
        x="TotalSalesDollars",
        y="Description",
        orientation="h",
        
    )

    fig3.update_traces(
    marker_color="#9C27B0"  # Purple
)
    
    fig3.update_layout(
        yaxis={
            "categoryorder":
            "total ascending"
        }
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

with col4:

    low_vendors = (
        get_low_performing_vendors(df)
    )
    st.subheader(
    "Low Performing Vendors"
)
    fig4 = px.bar(
        low_vendors,
        x="StockTurnover",
        y="VendorName",
        orientation="h",
        color="StockTurnover",
        color_continuous_scale="Reds",
        
    )

    fig4.update_layout(
        yaxis={
            "categoryorder":
            "total ascending"
        }
    )

    st.plotly_chart(
        fig4,
        use_container_width=True
    )



st.subheader(
    "Brands for Promotional or Pricing Adjustments"
)

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

promotion_brands = (
    get_promotion_opportunities(df)
)

# Create category column
brand_performance["Target Brand"] = "no"

brand_performance.loc[
    brand_performance["Description"].isin(
        promotion_brands["Description"]
    ),
    "Target Brand"
] = "yes"

fig5 = px.scatter(
    brand_performance[
        brand_performance["TotalSalesDollars"] < 1000
    ],
    x="TotalSalesDollars",
    y="ProfitMargin",
    color="Target Brand",
    hover_name="Description",
    color_discrete_map={
        "no": "#1F3A5F",   # Dark Blue
        "yes": "#FF4D4D"   # Red
    }
)


fig5.add_vline(
    x=low_sales_threshold,
    line_dash="dash"
)

fig5.add_hline(
    y=high_margin_threshold,
    line_dash="dash"
)

st.plotly_chart(
    fig5,
    use_container_width=True
)





st.divider()

