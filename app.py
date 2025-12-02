import streamlit as st
import pandas as pd
import plotly.express as px

# -------- PAGE CONFIG --------
st.set_page_config(
    page_title="Forecasting Medicine Requirements for a Hospital",
    layout="wide"
)

# -------- DATA LOADING --------
@st.cache_data
def load_data():
    meds = pd.read_csv("medication_summary.csv")
    afc = pd.read_csv("actual_forecast_combined.csv")

    # Convert Month -> Year in meds (if Month exists)
    if "Month" in meds.columns:
        meds["Month"] = pd.to_datetime(meds["Month"], errors="coerce")
        meds["Year"] = meds["Month"].dt.year

        # 🔹 Keep only 2020–2025 in medication summary
        meds = meds[(meds["Year"] >= 2020) & (meds["Year"] <= 2025)]

    # Ensure Year is numeric in afc
    if "Year" in afc.columns:
        afc["Year"] = pd.to_numeric(afc["Year"], errors="coerce")

        # 🔹 Keep only 2020–2025 in Actual/Forecast combined
        afc = afc[(afc["Year"] >= 2020) & (afc["Year"] <= 2025)]

    return meds, afc


meds, afc = load_data()

has_total_cost = "TOTALCOST" in meds.columns
has_encounterclass = "ENCOUNTERCLASS" in meds.columns

# -------- SIDEBAR NAV --------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Dashboard Overview",
        "Forecasting by Year",
        "Department Usage",
        "Executive Summary"
    ]
)

# =========================================================
# PAGE 1: DASHBOARD OVERVIEW
# =========================================================
if page == "Dashboard Overview":
    st.title("Forecasting Medicine Requirements for a Hospital")
    st.subheader("Overview of Medicine Usage and Key Metrics")

    total_dispenses = meds["DISPENSES"].sum()
    unique_meds = meds["DESCRIPTION"].nunique()
    total_cost = meds["TOTALCOST"].sum() if has_total_cost else None

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Medicines Dispensed", f"{int(total_dispenses):,}")
    c2.metric("Unique Medicines", f"{unique_meds:,}")
    if total_cost is not None:
        c3.metric("Total Cost of Medicines", f"${int(total_cost):,}")
    else:
        c3.metric("Total Cost of Medicines", "N/A")

    st.markdown("### Top Medicines Dispensed – 5-Year Trend")

    # Top 5 medicines by total dispenses
    top_meds = (
        meds.groupby("DESCRIPTION")["DISPENSES"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .index
    )
    meds_top = meds[meds["DESCRIPTION"].isin(top_meds)].copy()

    if "Year" in meds_top.columns:
        fig = px.bar(
            meds_top,
            x="Year",
            y="DISPENSES",
            color="DESCRIPTION",
            barmode="group",
            labels={"DISPENSES": "Dispenses", "Year": "Year"},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Year column not available for trend chart.")

# =========================================================
# PAGE 2: FORECASTING BY YEAR
# =========================================================
elif page == "Forecasting by Year":
    st.title("Medicine Forecasting by Year")

    # 1) Find medicines that have BOTH Actual and Forecast values
    type_counts = (
        afc.groupby("Medicine")["Type"]
        .nunique()
        .reset_index()
    )

    # Only medicines with at least 2 types (Actual + Forecast)
    valid_meds = type_counts[type_counts["Type"] >= 2]["Medicine"]
    med_list = sorted(valid_meds.dropna().unique())

    # 2) Sidebar dropdown – give it a UNIQUE key
    selected_medicine = st.sidebar.selectbox(
        "Select Medicine",
        med_list,
        key="forecast_select_medicine"
    )

    # 3) Filter data for the selected medicine
    df_med = afc[afc["Medicine"] == selected_medicine].copy()
    df_med = df_med.sort_values("Year")

    st.markdown(f"### Actual vs Forecast for: **{selected_medicine}**")

    # 4) Plot – give chart a UNIQUE key
    fig = px.bar(
        df_med,
        x="Year",
        y="Value",
        color="Type",  # Actual vs Forecast
        barmode="group",
        category_orders={"Type": ["Actual", "Forecast"]},
        labels={"Value": "Actual and Forecast Value"},
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="forecast_by_year_chart"
    )


# =========================================================
# PAGE 3: DEPARTMENT USAGE
# =========================================================
elif page == "Department Usage":
    st.title("Medicine Usage by Department")

    if has_encounterclass:
        dept_summary = (
            meds.groupby("ENCOUNTERCLASS", as_index=False)["DISPENSES"]
            .sum()
            .sort_values("DISPENSES", ascending=False)
        )

        fig_dept = px.bar(
            dept_summary,
            x="ENCOUNTERCLASS",
            y="DISPENSES",
            labels={"ENCOUNTERCLASS": "Encounter Type", "DISPENSES": "Total Dispenses"},
        )
        st.plotly_chart(fig_dept, use_container_width=True)

        st.markdown("#### Top Medicines within Each Department (first 50 rows)")
        top_by_dept = (
            meds.groupby(["ENCOUNTERCLASS", "DESCRIPTION"], as_index=False)["DISPENSES"]
            .sum()
            .sort_values(["ENCOUNTERCLASS", "DISPENSES"], ascending=[True, False])
        )
        st.dataframe(top_by_dept.head(50), use_container_width=True)
    else:
        st.info("ENCOUNTERCLASS column not found in medication_summary.csv")

# =========================================================
# PAGE 4: EXECUTIVE SUMMARY
# =========================================================
elif page == "Executive Summary":
    st.title("Executive Summary Dashboard")
    st.subheader("Key Insights from Medicine Inventory and Usage Analysis")

    total_dispenses = meds["DISPENSES"].sum()
    unique_meds = meds["DESCRIPTION"].nunique()
    total_cost = meds["TOTALCOST"].sum() if has_total_cost else None

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Medicines Dispensed", f"{int(total_dispenses):,}")
    c2.metric("Unique Medicines", f"{unique_meds:,}")
    if total_cost is not None:
        c3.metric("Total Cost of Medicines", f"${int(total_cost):,}")
    else:
        c3.metric("Total Cost of Medicines", "N/A")

    left, right = st.columns(2)

    if has_total_cost:
        cost_group = (
            meds.groupby("DESCRIPTION", as_index=False)["TOTALCOST"]
            .sum()
            .sort_values("TOTALCOST", ascending=False)
            .head(10)
        )
        fig_cost = px.bar(
            cost_group,
            x="TOTALCOST",
            y="DESCRIPTION",
            orientation="h",
            labels={"TOTALCOST": "Total Cost", "DESCRIPTION": "Medicine"},
        )
        left.markdown("#### Top Costliest Medicines")
        left.plotly_chart(fig_cost, use_container_width=True)

    if has_encounterclass:
        dept_summary = (
            meds.groupby("ENCOUNTERCLASS", as_index=False)["DISPENSES"]
            .sum()
            .sort_values("DISPENSES", ascending=False)
        )
        fig_dept = px.bar(
            dept_summary,
            x="ENCOUNTERCLASS",
            y="DISPENSES",
            labels={"ENCOUNTERCLASS": "Encounter Type", "DISPENSES": "Total Dispenses"},
        )
        right.markdown("#### Medicine Usage by Department")
        right.plotly_chart(fig_dept, use_container_width=True)

    st.markdown("### Narrative Insights")
    st.write(
        f"""
- **{int(total_dispenses):,}** medicine units dispensed across **{unique_meds}** unique medicines.
- Ambulatory / wellness and other high-use departments can be identified from the department usage view.
- Forecasting page compares **Actual vs Forecast** values for each medicine across years.
- High-cost medicines can be targeted for tighter inventory and budget control.
"""
    )
