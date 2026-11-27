'''
Streamlit dashboard
This file only handles display. Every number comes from src/queries.py
which runs the SQL files in sql/

to run: streamlit run app.py
'''

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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

@st.cache_data
def load_state():
    return queries.state_latest()

@st.cache_data
def load_region():
    return queries.region_trends()

@st.cache_data
def load_pandemic():
    return queries.pandemic_impact()

##Helping functions

#shade recessions that overlap dates being shown on a chart
def shade_recessions(fig, dates, **vrect_kwargs):
    for start, end in RECESSIONS:
        if pd.Timestamp(end) >= dates.min() and pd.Timestamp(start) <= dates.max():
            fig.add_vrect(
                x0=start, x1=end, fillcolor="grey", opacity=0.15,
                line_width=0, **vrect_kwargs,
            )

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
    shade_recessions(fig, view["obs_date"], row="all", col=1)
    
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


TREND_COLORS = {"Improving": "#2ca02c", "Worsening": "#d62728", "Flat": "#7f7f7f"}
#hoizontal bars, one per state sorted largest to smallest value
def build_states_chart(view, metric_col, axis_title, suffix):
    ordered = view.sort_values(metric_col, ascending=False)
    fig = px.bar(
        ordered,
        x=metric_col,
        y="state_name",
        orientation="h",
        color="trend",
        color_discrete_map=TREND_COLORS,
        category_orders={
            "state_name": ordered["state_name"].tolist(),
            "trend": ["Improving", "Worsening", "Flat"],
        },
        hover_data={
            "region": True,
            "unemployment_rate": ":.1f",
            "rate_year_ago": ":.1f",
            "change_vs_year_ago": ":+.1f",
            "state_name": False,
            "trend": False,
        },
        labels={
            "unemployment_rate": "Rate (%)",
            "rate_year_ago": "Year ago (%)",
            "change_vs_year_ago": "Change (pts)",
            "region": "Region",
        },
    )
    fig.update_yaxes(autorange="reversed", title_text="")
    fig.update_xaxes(title_text=axis_title, ticksuffix=suffix)
    fig.update_layout(
        #taller when more states are shown
        height=max(300, 18*len(ordered)+100),
        legend_title_text="Vs a year ago",
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig

REGION_COLORS = {
    "Midwest": "#1f77b4",
    "Northeast": "#ff7f0e",
    "South": "#2ca02c",
    "West": "#9467bd"
}
#build chart for regions: one line per regions showing either avg rate or gap vs national rate
def build_regions_chart(view, show_gap):
    metric_col = "gap_vs_national" if show_gap else "avg_unemployment_rate"
    hover = "%{y:+.1f} pts" if show_gap else "%{y:.1f}%"

    fig = go.Figure()
    #for each region
    for region in sorted(view["region"].unique()):
        region_data = view[view["region"] == region]
        fig.add_trace(
            go.Scatter(
                x=region_data["obs_date"], y=region_data[metric_col], name=region,
                line=dict(color=REGION_COLORS.get(region, "#333333"), width=2),
                hovertemplate=hover
            )
        )

    if show_gap:
        #0 line indicating same as national 
        fig.add_hline(y=0, line_dash="dot", line_color="grey")
    else:
        #national rate is same for every region so keep to one row per month
        national = view.drop_duplicates("obs_date").sort_values("obs_date")
        fig.add_trace(
            go.Scatter(
                x=national["obs_date"], y=national["national_rate"], name="National",
                line=dict(color="black", width=2, dash="dash"), hovertemplate="%{y:.1f}%",
            )
        )
    shade_recessions(fig, view["obs_date"])
    fig.update_yaxes(
        title_text="Percentage points vs national" if show_gap else "Unemployment rate",
        ticksuffix="" if show_gap else "%",
    )
    fig.update_layout(
        height=520,
        hovermode="x unified",
        legend=dict(orientation="h", y=0.15),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig

#build a dumbbell chart where each state has a line from feb 2020 rate to peak
def build_hardest_hit_chart(view):
    ordered = view.sort_values("increase", ascending=False)
    names = ordered["state_name"].tolist()

    #connecting line (one per state) with a gap between states
    line_x, line_y = [], []
    for _, row in ordered.iterrows():
        line_x += [row["baseline_rate"], row["peak_rate"], None]
        line_y += [row["state_name"], row["state_name"], None]
    
    fig = go.Figure()
    #connecting line
    fig.add_trace(
        go.Scatter(x=line_x, y=line_y, mode="lines", line=dict(color="#bbbbbb", width=2), hoverinfo="skip", showlegend=False)
    )
    #baseline rate blue dot
    fig.add_trace(
        go.Scatter(
            x=ordered["baseline_rate"], y=names, mode="markers", name="Feb 2020",
            marker=dict(color="#1f77b4", size=8),
            hovertemplate="%{y}: %{x:.1f}%<extra>Feb 2020</extra>",
        )
    )
    #peak rate red dot
    fig.add_trace(
        go.Scatter(
            x=ordered["peak_rate"], y=names, mode="markers", name="Peak",
            marker=dict(color="#d62728", size=8),
            customdata=ordered["peak_date"].dt.strftime("%b %Y"),
            hovertemplate="%{y}: %{x:.1f}%<br>Peak month: %{customdata}<extra>Peak</extra>",
        )
    )
    #updated axes
    fig.update_yaxes(categoryorder="array", categoryarray=names, autorange="reversed", title_text="")
    fig.update_xaxes(title_text="Unemployment rate", ticksuffix="%")
    fig.update_layout(
        height=max(300, 18*len(ordered)+100),
        legend=dict(orientation="h", y=1.02, yanchor="bottom"),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig

#build scatter plot of the size of increase against months to recover with state labels and region colors
def build_recovery_chart(view):
    #get only states that have recovered rates
    recovered = view.dropna(subset=["months_to_recover"])
    fig = px.scatter(
        recovered,
        x="increase",
        y="months_to_recover",
        color="region",
        color_discrete_map=REGION_COLORS,
        text="state_code",
        hover_name="state_name",
        hover_data={"state_code": False, "increase": ":.1f", "months_to_recover":True},
        labels={
            "increase": "Increase (pts)",
            "months_to_recover": "Months to recover",
            "region": "Region",
        },
    )
    #update axes 
    fig.update_traces(textposition="top center", marker=dict(size=10))
    fig.update_xaxes(title_text="Increase in unemployment rate (percentage points)")
    fig.update_yaxes(title_text="Months from peak to recovery")
    fig.update_layout(height=550, legend_title_text="Region", margin=dict(l=10, r=10, t=30, b=10))
    return fig

##Set up pages

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

def page_states():
    st.title("State unemployment")

    data = load_state()
    as_of = data["as_of_date"].max()
    st.caption(f"What states have the highest unemployment now and who's improving? Latest data: {as_of:%B %Y}. Each state is compared with the same month a year earlier.")

    #controls - interactive components
    control_left, control_right = st.columns(2)
    regions = sorted(data["region"].unique())
    #ability to select regions you want to see in bar chart
    selected = control_left.multiselect("Regions", regions, default=regions)
    #ability to select which metric you want to see
    metric_label = control_right.radio(
        "Show", ["Unemployment rate", "Change vs a year ago"], horizontal=True
    )
    
    #select data within selected region (^^) and warning if empty
    view = data[data["region"].isin(selected)]
    if view.empty:
        st.warning("Select at least one region.")
        return

    #headline numbers for selected regions
    highest = view.loc[view["unemployment_rate"].idxmax()]
    lowest = view.loc[view["unemployment_rate"].idxmin()]
    improving = int((view["trend"] == "Improving").sum())
    worsening = int((view["trend"] == "Worsening").sum())

    cards = st.columns(3)
    cards[0].metric(f"Highest: {highest.state_name}", f"{highest.unemployment_rate:.1f}%")
    cards[1].metric(f"Lowest: {lowest.state_name}", f"{lowest.unemployment_rate:.1f}%")
    cards[2].metric(
        "Improving / worsening", f"{improving} / {worsening}",
        help="Number of states with a lower / higher rate than a year ago.",
    )

    #chart
    if metric_label == "Unemployment rate":
        metric_col, axis_title, suffix = "unemployment_rate", "Unemployment rate", "%"
    else:
        metric_col, axis_title, suffix = "change_vs_year_ago", "Change vs a year ago (percentage points)", ""
    st.plotly_chart(build_states_chart(view, metric_col, axis_title, suffix))

    with st.expander("View and download the data"):
        st.caption("The rank column compares each state with all 51, regardless of region.")
        table = view.sort_values("rank_highest_unemployment")
        st.dataframe(table, hide_index=True)
        st.download_button(
            "Download as CSV",
            view.to_csv(index=False).encode("utf-8"),
            file_name="state_unemployment.csv",
            mime="text/csv",
        )

def page_regions():
    st.title("Regions Over Time vs National Rate")

    st.caption(
        "Average unemployment rate across the states in each Census region, compared with the national rate. Shaded bands are US recessions (NBER)."
    )

    data = load_region()

    #controls - interactive components
    control_left, control_right = st.columns(2)
    regions = sorted(data["region"].unique())
    #ability to select regions you want to see in bar chart
    selected = control_left.multiselect("Regions", regions, default=regions)
    #ability to select which metric you want to see
    metric_label = control_right.radio(
        "Show", ["Average unemployment rate", "Gap vs national rate"], horizontal=True
    )
    
    #slider for date
    min_date = data["obs_date"].min().to_pydatetime()
    max_date = data["obs_date"].max().to_pydatetime()
    start, end = st.slider(
        "Date range", min_value=min_date, max_value=max_date,
        value=(min_date, max_date), format="MMM YYYY",
    )

    #select data within region and date selected, if empty send warning 
    view = data[
        data["region"].isin(selected)
        & (data["obs_date"] >= start)
        & (data["obs_date"] <= end)
    ]
    if view.empty:
        st.warning("Select at least one region and a date range with data.")
        return

    #latest value for each selected region using full dataset
    latest_date = data["obs_date"].max()
    latest = data[(data["obs_date"] == latest_date) & data["region"].isin(selected)]
    latest = latest.sort_values("region")
    cards = st.columns(len(latest)) if len(latest) else []
    for card, (_, row) in zip(cards, latest.iterrows()):
        delta = None if pd.isna(row["gap_vs_national"]) else f"{row['gap_vs_national']:+.1f} pts vs national"
        card.metric(
            f"{row['region']} ({latest_date:%b %Y})",
            f"{row['avg_unemployment_rate']:.1f}%",
            delta,
            delta_color="off",
        )
    peak = view.loc[view["avg_unemployment_rate"].idxmax()]
    st.markdown(
        f"**In the selected range, the highest regional average was {peak['avg_unemployment_rate']:.1f}% in the {peak['region']} in {peak['obs_date']:%b %Y}.**"
    )

    st.plotly_chart(build_regions_chart(view, show_gap=(metric_label == "Gap vs national rate")))

    with st.expander("About this view"):
        st.markdown(
            "- **Regional average:** a simple average of the state unemployement rates in each Census region. It is not weighted by population or labor force, so large and small states count equally. \n"
            "- **National rate:** the official national unemployment rate, which is calculated separately, so a gap of zero doesn't mean a region matches the nation exactly. \n"
            "- **Gap:** the regional average minus the national rate, in percentage points."
        )

    with st.expander("View and download the data"):
        table = view.sort_values(["obs_date", "region"])
        st.dataframe(table, hide_index=True)
        st.download_button(
            "Download as CSV",
            view.to_csv(index=False).encode("utf-8"),
            file_name="regional_unemployment.csv",
            mime="text/csv",
        )

def page_pandemic():
    st.title("Pandemic Impact")
    st.caption(
        "How far each state's unemployment rate rose from February 2020 to its peak (through December 2021), and how long it took to get back within 0.5 percentage points of the February 2020 level."
    )

    data = load_pandemic()

    #option to select specific region, if no region selected send warning 
    regions = sorted(data["region"].unique())
    selected = st.multiselect("Regions", regions, default=regions)
    view = data[data["region"].isin(selected)]
    if view.empty:
        st.warning("Select at least one region.")
        return
    
    #headline numbers for selected region(s)
    #find row of state with largest increase in rate and all states with record of recovery
    hardest = view.loc[view["increase"].idxmax()]
    recovered = view.dropna(subset=["months_to_recover"])

    cards = st.columns(4)
    cards[0].metric(f"Largest increase: {hardest['state_name']}", f"+{hardest['increase']:.1f} pts")
    cards[1].metric("Median increase", f"+{view['increase'].median():.1f} pts")
    if recovered.empty:
        cards[2].metric("Slowest recover", "n/a")
        cards[3].metric("Median recovery time", "n/a")
    else:
        slowest = recovered.loc[recovered["months_to_recover"].idxmax()]
        cards[2].metric(
            f"Slowest recovery: {slowest['state_name']}", f"{int(slowest['months_to_recover'])} months"
        )
        cards[3].metric("Median recovery time", f"{recovered['months_to_recover'].median():0f} months")

    #find number of states that didn't recover (if any)
    not_recovered = len(view) - len(recovered)
    if not_recovered:
        st.info(F"{not_recovered} state(s) did not get back within 0.5 points of their February 2020 rate in this data.")
    
    #state lookup regardless of region
    st.subheader("Look up a state")
    prompt = "Choose a state"
    choice = st.selectbox("State", [prompt] + sorted(data["state_name"]))
    #if state is selected, find dara for state and add baseline rate, peak rate (+increase), and recovery date and months (if applicable)
    if choice != prompt:
        row = data[data["state_name"] == choice].iloc[0]
        detail = st.columns(4)
        detail[0].metric("February 2020", f"{row['baseline_rate']:.1f}%")
        detail[1].metric(
            f"Peak ({row['peak_date']:%b %Y})", f"{row['peak_rate']:.1f}%",
            f"+{row['increase']:.1f} pts", delta_color="inverse",
        )
        if pd.isna(row["recovery_date"]):
            detail[2].metric("Back neat February 2020 rate", "Not yet")
            detail[3].metric("Months from peak", "n/a")
        else:
            detail[2].metric("Back near February 2020 rate", f"{row['recovery_date']:%b %Y}")
            detail[3].metric("Months from peak", f"{int(row['months_to_recover'])}")
        st.caption(f"Ranked #{int(row['rank_by_increase'])} of {len(data)} states by size of increase.")

    #separate tabs for separate charts (hardest hit and recovery chart)
    tab_hit, tab_recovery = st.tabs(["Hardest hit", "Recovery speed"])
    with tab_hit:
        st.caption("Each line runs from a state's February 2020 rate (blue) to its peak(red).")
        st.plotly_chart(build_hardest_hit_chart(view))
    with tab_recovery:
        st.caption("States toward the upper right were hit hard and took longer to recover.")
        st.plotly_chart(build_recovery_chart(view))

    with st.expander("About this view"):
        st.markdown(
            "- **Baseline:** the state's unemployment rate in February 2020, just before the shock. \n"
            "- **Peak:** the highest rate between March 2020 and December 2021. \n"
            "- **Recovered:** the first month after the peak when the rate was back within 0.5 percentage points of the baseline. The 0.5 is a choice and it can be changed in `sql/pandemic_impact.sql`.\n"
            "- **Months to recover:** months from the peak month to the recovery month."
        )    

    with st.expander("View and download the data"):
        table = view.sort_values("rank_by_increase")
        st.dataframe(table, hide_index=True)
        st.download_button(
            "Download as CSV",
            view.to_csv(index=False).encode("utf-8"),
            file_name="pandemic_impact.csv",
            mime="text/csv",
        )


#add navigator for pages
PAGES = {
    "National": page_national,
    "States": page_states,
    "Regions": page_regions,
    "Pandemic": page_pandemic,
}

st.sidebar.title("US Economy Dashboard")
choice = st.sidebar.radio("Go To", list(PAGES))
st.sidebar.caption("Data: Federal Reserve Bank of St. Louis (FRED)")

PAGES[choice]()
