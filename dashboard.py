import streamlit as st
import pandas as pd
import plotly.express as px
from src.ai_summary import generate_ai_summary

# Page Configuration
st.set_page_config(
    page_title="Grade System Dashboard",
    layout="wide"
)

# Load Data
df = pd.read_csv("output/master_performance.csv")

# Title
st.image("assets\images.jpg", width=80)
st.title("📊 Automated Training Performance Dashboard")

# AI Summary
with st.container(border=True):
    st.subheader("🤖 Executive AI Summary")
    st.write(summary := generate_ai_summary(df))

# KPI Metrics
col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Students",
    len(df)
)

col2.metric(
    "Average Percentage",
    round(df["Percentage"].mean(), 2)
)

col3.metric(
    "Top Score",
    round(df["Percentage"].max(), 2)
)

# Top 10 Students
st.subheader("🏆 Top 10 Students")

top10 = df.sort_values(
    by="Rank"
).head(10)

st.dataframe(top10)

# Grade Distribution
st.subheader("📈 Grade Distribution")

fig = px.pie(
    df,
    names="Grade",
    hole=0.55,
    title="Grade Distribution"
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# Top 5 Students
st.subheader("⭐ Top 5 By Percentage")

top5 = df.sort_values(
    by="Percentage",
    ascending=False
).head(5)

st.dataframe(
    top5[["Name", "Percentage", "Rank"]]
)

# Weak Students
st.subheader("⚠️ Weak Students")

weak = df[
    df["Percentage"] < 40
]

st.dataframe(
    weak[["Name", "Percentage", "Grade"]]
)

# Complete Dataset
st.subheader("📋 Complete Student Data")

st.dataframe(df)