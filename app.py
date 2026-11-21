'''
Streamlit dashboard
This file only handles display. Every number comes from src/queries.py
which runs the SQL files in sql/

to run: streamlit run app.py
'''

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from src import queries

st.set_page_config(page_title="US Economy Dashboard", page_icon="📈", layout="wide")

#us recessions dated by National Bureau of Economic Research
#saved for shading on national chart for context
RECESSIONS = [
    ("2001-03-01", "2001-11-30"),
    ("2007-12-01", "2009-06-30"),
    ("2020-02-01", "2020-04-30"),
]

#get data --> run the query once then reuse the result on later clicks
@st.cache_data
def load_national():
    return queries.national_trends()

##Helping functions
#return latest value, its date, and value a year earlier for one column
def latest_with_year_ago(df, col):
    series = df.dropna(subset=[col])
    #return empty values if column is empty after removing na
    if series.empty:
        return None, None, None
    #data is sorted by date so find last row for most recent
    last = series.iloc[-1]
    #find the year ago date by subtracting 1 year from latest date and finding row 
    #in series with exactly that date and extracts value from col (as pandas series) (then pulls out as single raw value)
    year_ago_date = last['obs_date'] - pd.DateOffset(years=1)
    match = series.loc[series['obs_date'] == year_ago_date, col]
    year_ago = match.iloc[0] if not match.empty else None
    return last[col], last['obs_date'], year_ago

#show one headline number with its change vs a year ago
def metric_card(container, label, df, col, inverse: bool = False):
    value, date, year_ago = latest_with_year_ago(df, col)
    #check if data exists for col at date else n/a
    if value is None:
        container.metric(label, "n/a")
        return
    #if data for year and year ago date headline showing change
    delta = None if year_ago is None else f"{value - year_ago:+.1f} pts vs year ago"
    #inverse = a rise is bad (show in red), off = neutral grey
    container.metric(
        f"{label} ({date:%b %Y})",
        f"{value:.1f}%",
        delta,
        delta_color="inverse" if inverse else "off"
    )

#sentence about selected data range
def national_highlights(view):
    parts = []
    unemployment = view.dropna(subset=["unemployment_rate"])
    #if unemployment isnt empty after dropna find highest rate and summarize
    if not unemployment.empty:
        row = unemployment.loc[unemployment["unemployment_rate"].idxmax()]
        parts.append(f"unemployment peaked as {row.unemployment_rate:.1f}% in {row.obs_date:%b %Y}")
    #same as unemployment for inflation
    inflation = view.dropna(subset=["inflation_rate"])
    if not inflation.empty:
        row = inflation.loc[inflation["inflation_rate"].idxmax()]
        parts.append(f"inflation peaked at {row.inflation_rate:.1f}% in {row.obs_date:%b %Y}")
        if not parts:
            return ""
        return "In the selected range, " + " and ".join(parts) + "."
    
#create two stacked panels: labor market and prices on top, interest rates below
def build_national_chart(view):
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
        subplot_titles=("Unemployment and inflation", "Interest rates"),
    )

    lines = [
        #(row, column in the data, legend name, color)
        (1, "unemployment_rate", "Unemployment rate", "#1f77b4"),
        (1, "inflation_rate", "Inflation (CPI, year over year)", "#d62728"),
        (2, "fed_funds_rate", "Fed funds rate", "#2ca02c"),
        (2, "real_fed_funds_rate", "Real fed funds rate", "#9467bd"),
    ]
    for row, col, name, color in lines:
        fig.add_trace(
            go.Scatter(
                x=view["obs_date"], y=view[col], name=name,
                line=dict(color=color, width=2), hovertemplate="%{y:.1f}%",
            ),
            row=row, col=1
        )
    #shade recessions that overlap in selected range
    for start, end in RECESSIONS:
        if pd.Timestamp(end) >= view["obs_date"].min() and pd.Timestamp(start) <= view["obs_date"].max():
            fig.add_vrect(x0=start, x1=end, fillcolor="grey", opacity=0.15, line_width=0, row="all", col=1)
    
    #add a zero line
    fig.add_hline(y=0, line_dash="dot", line_color="grey", row=2, col=1)

    fig.update_yaxes(title_text="Percent", ticksuffix="%")
    fig.update_layout(
        height=650,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.1),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig

#Set up pages
def page_national():
    st.title("National trends")
    st.caption(
        "How unemployment, inflation, and interest rates have moved together. "
        "Shaded bands are US recessions (NBER)."

    )

    data = load_national()

    #headline numbers use the full dataset
    cards = st.columns(4)
    metric_card(cards[0], "Unemployment", data, "unemployment_rate", inverse=True)
    metric_card(cards[1], "Inflation", data, "inflation_rate", inverse=True)
    metric_card(cards[2], "Fed funds rate", data, "fed_funds_rate")
    metric_card(cards[3], "Real fed funds rate", data, "real_fed_funds_rate")

    #date range filter slider
    min_date = data["obs_date"].min().to_pydatetime()
    max_date = data["obs_date"].max().to_pydatetime()
    start, end = st.slider(
        "Date range", min_value=min_date, max_value=max_date,
        value=(min_date, max_date), format="MMM YYYY",
    )
    #set up view to be between dates indicated on slider
    view = data[(data["obs_date"] >= start) & (data["obs_date"] <= end)]

    if view.empty:
        st.warning("No data in that range.")
        return
    
    highlight = national_highlights(view)
    if highlight:
        st.markdown(f"**{highlight}**")
    
    st.plotly_chart(build_national_chart(view))

    with st.expander("About these measures"):
        st.markdown(
            "- **Unemployment rate:** share of the labor force without a job and looking for one.\n"
            "- **Inflation:** how much the Consumer Price Index (all items) rose compared with the same month a year earlier.\n"
            "- **Fed funds rate:** the interest rate banks charge each other overnight, which the Federal Reserve steers.\n"
            "- **Real fed funds rate:** the fed funds rate minus inflation. When it is below zero, borrowing costs are lower than the rate prices are rising. This is an approximation that uses past inflation.\n\n"
            "Source: Federal Reserve Bank of St. Louis (FRED)."
        )

    with st.expander("View and download the data"):
        st.dataframe(view, hide_index=True)
        st.download_button(
            "Download as CSV",
            view.to_csv(index=False).encode("utf-8"),
            file_name="national_trends.csv",
            mime="text/csv",
        )

#add navigator for pages
PAGES = {
    "National": page_national,
}

st.sidebar.title("US Economy Dashboard")
choice = st.sidebar.radio("Go To", list(PAGES))
st.sidebar.caption("Data: Federal Reserve Bank of St. Louis (FRED)")

PAGES[choice]()
