import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Global Temperature Analytics", layout="wide")

st.markdown("""
    <style>
    /* Import a nice, modern Google Font (Nunito) */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap');

    /* Sky blue to faded summer yellow gradient */
    .stApp {
        background: linear-gradient(to bottom, #87CEFA 0%, #FFF4C2 100%);
        background-attachment: fixed;
    }
    
    /* Apply custom font and ensure text is a readable dark slate */
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Nunito', sans-serif !important;
    }
    
    h1, h2, h3, p, span, label {
        color: #1E293B !important; 
    }
    
    /* Bright summer gradient for the slider track */
    div.stSlider > div[data-baseweb="slider"] > div > div > div:nth-child(1) {
        background: linear-gradient(to right, #3A7CA5, #FF7E67) !important;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_excel("combined_temperature.xlsx")
    
    # Clean up years and strictly cap the data at 2022
    df["Year"] = df["Year"].astype(int)
    df = df[df["Year"] <= 2022] 
    
    df["Decade"] = (df["Year"] // 10) * 10
    df = df.sort_values(["Country", "Year"])

    if "Annual Mean" in df.columns:
        df["Baseline"] = df.groupby("Country")["Annual Mean"].transform("mean")
        df["Anomaly"] = df["Annual Mean"] - df["Baseline"]
    else:
        df["Anomaly"] = 0

    df["5-yr smooth anomaly"] = df.groupby("Country")["Anomaly"].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    return df

df = load_data()

HEAT_SCALE = [[0.00, "#3A7CA5"], [0.35, "#8BAF7C"], [0.55, "#F5C842"], [0.75, "#FF7E67"], [1.00, "#E63946"]]
COUNTRY_COLORS = ["#E63946", "#3A7CA5", "#2A9D8F", "#F4A261", "#8338EC"]
yr_min_data = int(df["Year"].min())
yr_max_data = int(df["Year"].max()) # This will now be capped at 2022

st.title("Global Temperature Analytics")
st.write(f"Surface temperature anomalies from {yr_min_data} to {yr_max_data}")

st.subheader("Global Year Range Filter")
yr_range = st.slider("Select Year Range", min_value=yr_min_data, max_value=yr_max_data, value=(yr_min_data, yr_max_data))

filtered_df = df[(df["Year"] >= yr_range[0]) & (df["Year"] <= yr_range[1])]

st.subheader("Temperature anomalies by country (1970–2022)")
yearly = df[df["Year"] >= 1970].copy()
yearly["Year"] = yearly["Year"].astype(str)

fig_map = px.choropleth(
    yearly, locations="Code", color="Anomaly", hover_name="Country",
    animation_frame="Year", color_continuous_scale=HEAT_SCALE,
    range_color=[-2, 2.5], template="plotly_white"
)
fig_map.update_geos(
    showframe=False, showcoastlines=True, 
    projection_type="natural earth",
    bgcolor="rgba(0,0,0,0)",
    showland=True, landcolor="#F8F9FA",
    showocean=True, oceancolor="rgba(0,0,0,0)" # Oceans blend into the gradient
)
fig_map.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20))
st.plotly_chart(fig_map, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Global average anomaly over time")
    global_avg = filtered_df.groupby("Year")[["Anomaly", "5-yr smooth anomaly"]].mean().reset_index()
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=global_avg["Year"], y=global_avg["Anomaly"], mode="lines", name="Annual avg", line=dict(color="#F4A261", dash="dot"), opacity=0.5))
    fig_trend.add_trace(go.Scatter(x=global_avg["Year"], y=global_avg["5-yr smooth anomaly"], mode="lines", name="5-year trend", line=dict(color="#E63946", width=2.5)))
    fig_trend.update_layout(
        template="plotly_white", 
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
        margin=dict(t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col2:
    st.subheader("Anomaly distribution by decade")
    fig_box = go.Figure()
    decades = sorted(df["Decade"].dropna().unique())
    
    for d in decades:
        d_df = df[df["Decade"] == d]
        clr = "#FF7E67" if d >= 1980 else "#3A7CA5"
        fig_box.add_trace(go.Box(y=d_df["Anomaly"], name=str(int(d)) + "s", marker_color=clr))
        
    fig_box.update_layout(
        template="plotly_white", 
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
        margin=dict(t=20, b=20), showlegend=False
    )
    st.plotly_chart(fig_box, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Country comparison — smoothed anomaly")
    all_countries = sorted(df["Country"].unique())
    selected_countries = st.multiselect("Select up to 5 countries:", all_countries, default=all_countries[:4])
    
    fig_comp = go.Figure()
    for i, country in enumerate(selected_countries[:5]):
        c_df = filtered_df[filtered_df["Country"] == country]
        fig_comp.add_trace(go.Scatter(x=c_df["Year"], y=c_df["5-yr smooth anomaly"], mode="lines", name=country, line=dict(color=COUNTRY_COLORS[i % len(COUNTRY_COLORS)], width=3)))
        
    fig_comp.update_layout(
        template="plotly_white", 
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
        margin=dict(t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig_comp, use_container_width=True)

with col4:
    st.subheader("Highest anomalies by year")
    sel_year = st.slider("Select year:", min_value=yr_min_data, max_value=yr_max_data, value=yr_max_data)
    
    top_10 = df[df["Year"] == sel_year].dropna(subset=["Anomaly"]).sort_values("Anomaly", ascending=False).head(10).sort_values("Anomaly", ascending=True)
    
    fig_bar = go.Figure(go.Bar(
        x=top_10["Anomaly"], y=top_10["Country"], orientation="h",
        marker=dict(color=top_10["Anomaly"], colorscale=HEAT_SCALE, cmin=-1.0, cmax=2.5)
    ))
    fig_bar.update_layout(
        template="plotly_white", 
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
        margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig_bar, use_container_width=True)