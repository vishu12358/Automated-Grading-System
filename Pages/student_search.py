import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
st.image("assets\images.jpg", width=80)

st.set_page_config(page_title="Student Search", layout="wide")

# ------------------------------------
# Load Data
# ------------------------------------
df = pd.read_csv("output/master_performance.csv")
df["Percentage"] = pd.to_numeric(df["Percentage"], errors="coerce").clip(0, 100)

st.title("🔍 Student Search & Performance Profile")

quiz_columns = [
    "Quiz1",
    "Quiz2",
    "Quiz3",
    "Quiz4",
    "Quiz5",
    "Quiz6",
    "Quiz7"
]

# ------------------------------------
# Search Student
# ------------------------------------

student_names = df["Name"].dropna().astype(str).unique().tolist()
student_names.sort(key=lambda x: x.lower())
student = st.selectbox(
    "Select Student",
    student_names
)

student_data = df[df["Name"] == student].iloc[0]

st.divider()

# ------------------------------------
# Student Information
# ------------------------------------

col1, col2 = st.columns([1,2])

with col1:

    st.image(
        "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
        width=150
    )

with col2:

    st.subheader(student)

    st.write(f"📧 **Email:** {student_data['Email']}")
    st.write(f"🏅 **Grade:** {student_data['Grade']}")
    st.write(f"📈 **Percentage:** {student_data['Percentage']:.2f}%")
    st.write(f"🏆 **Rank:** {int(student_data['Rank'])}")
    st.write(f"📝 **Total Marks:** {student_data['Total_Marks']}")

st.divider()

# ------------------------------------
# KPI Cards
# ------------------------------------

c1,c2,c3,c4 = st.columns(4)

c1.metric("Grade", student_data["Grade"])
c2.metric("Percentage", f"{student_data['Percentage']:.2f}%")
c3.metric("Rank", int(student_data["Rank"]))
c4.metric("Total Marks", int(student_data["Total_Marks"]))

st.divider()

# ------------------------------------
# Quiz Performance
# ------------------------------------

marks = pd.DataFrame({
    "Quiz": quiz_columns,
    "Marks":[student_data[q] for q in quiz_columns]
})

fig = px.bar(
    marks,
    x="Quiz",
    y="Marks",
    color="Marks",
    text="Marks",
    title="Quiz-wise Performance"
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------
# Radar Chart
# ------------------------------------

fig2 = go.Figure()

fig2.add_trace(go.Scatterpolar(
    r=marks["Marks"],
    theta=marks["Quiz"],
    fill='toself',
    name=student
))

fig2.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True
        )
    ),
    title="Performance Radar"
)

st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------
# Strengths & Weaknesses
# ------------------------------------

highest = marks.loc[marks["Marks"].idxmax()]
lowest = marks.loc[marks["Marks"].idxmin()]

col1,col2 = st.columns(2)

with col1:
    st.success(
        f"""
### 💪 Strength

Best Quiz : **{highest['Quiz']}**

Marks : **{highest['Marks']}**
"""
    )

with col2:
    st.error(
        f"""
### 📉 Weak Area

Needs Improvement : **{lowest['Quiz']}**

Marks : **{lowest['Marks']}**
"""
    )

st.divider()

# ------------------------------------
# AI Recommendation
# ------------------------------------

st.subheader("🤖 AI Performance Review")

recommendation = []

if student_data["Percentage"] >= 80:
    recommendation.append("Excellent performance. Maintain consistency.")

elif student_data["Percentage"] >= 60:
    recommendation.append("Good performance. Focus on improving weaker quizzes.")

else:
    recommendation.append("Needs improvement. Attend extra practice sessions.")

recommendation.append(
    f"Revise {lowest['Quiz']} regularly."
)

recommendation.append(
    "Attempt weekly mock tests."
)

recommendation.append(
    "Practice previous assessment questions."
)

for item in recommendation:
    st.info(item)

# ------------------------------------
# Student Data
# ------------------------------------

st.subheader("📋 Complete Student Record")

st.dataframe(
    student_data.to_frame().T,
    use_container_width=True,
    hide_index=True
)

# ------------------------------------
# Download Report
# ------------------------------------

csv = student_data.to_frame().T.to_csv(index=False)

st.download_button(
    "⬇ Download Student Report",
    csv,
    f"{student}_Report.csv",
    "text/csv"
)