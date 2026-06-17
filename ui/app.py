import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import sys
import os


sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)


from main import run_agent


# -------------------------
# SESSION
# -------------------------

if "result" not in st.session_state:
    st.session_state.result = None



# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(
    page_title="Incident AI Agent",
    page_icon="🤖",
    layout="wide"
)


st.title(
    "🤖 Autonomous Incident Diagnosis Agent"
)

st.caption(
    "AI based incident detection, explanation and remediation"
)



# -------------------------
# PDF
# -------------------------

def create_pdf(anomalies):


    pdf = FPDF()

    pdf.add_page()


    pdf.set_auto_page_break(
        auto=True,
        margin=15
    )


    pdf.set_font(
        "Arial",
        size=11
    )


    pdf.cell(
        0,
        10,
        "Incident Anomaly Report",
        ln=True
    )


    pdf.ln(5)



    anomalies = list(
        dict.fromkeys(anomalies)
    )


    for i, item in enumerate(anomalies,1):

        text = str(item)


        text = (
            text
            .encode(
                "ascii",
                "ignore"
            )
            .decode()
        )


        # split long words

        words = text.split()

        line = ""


        pdf.write(
            7,
            f"{i}. "
        )


        for word in words:


            if len(line + word) > 60:

                pdf.write(
                    7,
                    line
                )

                pdf.ln(7)

                line = word + " "

            else:

                line += word + " "



        pdf.write(
            7,
            line
        )

        pdf.ln(8)



    path = tempfile.mktemp(
        suffix=".pdf"
    )


    pdf.output(path)


    return path





# -------------------------
# UPLOAD
# -------------------------

file = st.file_uploader(
    "📂 Upload Incident CSV",
    type=["csv"]
)



if file:


    df = pd.read_csv(file)


    df.columns = [
        c.strip()
        for c in df.columns
    ]


    st.subheader(
        "📥 Uploaded Data"
    )


    st.dataframe(
        df.head(15),
        use_container_width=True
    )



    if st.button(
        "🚀 Analyze Incident",
        type="primary"
    ):


        with st.spinner(
            "Agents analysing..."
        ):


            st.session_state.result = run_agent(df)



        st.success(
            "Analysis Completed"
        )





# -------------------------
# DISPLAY RESULT
# -------------------------

if st.session_state.result is not None:


    result = st.session_state.result


    anomaly = result["anomaly"]

    rca = result["rca"]

    remediation = result["remediation"]



    anomalies = list(
        dict.fromkeys(
            anomaly["anomalies"]
        )
    )


    actions = list(
        dict.fromkeys(
            remediation["actions"]
        )
    )



    # =========================
    # SUMMARY
    # =========================

    st.header(
        "📄 Final Incident Summary"
    )


    summary = anomaly["summary"]



    c1,c2,c3 = st.columns(3)


    c1.metric(
        "Total Logs",
        summary["total_logs"]
    )


    c2.metric(
        "Applications",
        len(summary["applications"])
    )


    c3.metric(
        "Issues",
        len(anomalies)
    )


    apps = [
        str(x)
        for x in summary["applications"]
        if pd.notna(x)
    ]


    st.info(
        f"""
Affected Applications:

{", ".join(apps)}

Incident analysis completed.
"""
    )



    # =========================
    # REMEDIATION
    # =========================


    st.header(
        "🛠 Recommended Remediation"
    )


    for action in actions:

        st.success(
            "✓ " + action
        )



    # =========================
    # RCA
    # =========================


    st.header(
        "🔍 Incident Explanation"
    )


    explanation = str(
        rca["root_cause"]
    )


    explanation = (
        explanation
        .replace("|",".")
    )


    explanation = ".".join(
        explanation.split(".")[:2]
    )


    st.write(
        explanation
    )



    # =========================
    # PDF
    # =========================


    st.header(
        "📥 Incident Evidence"
    )


    pdf_path = create_pdf(
        anomalies
    )


    with open(
        pdf_path,
        "rb"
    ) as f:


        st.download_button(

            "⬇️ Download Anomaly PDF",

            f,

            file_name="incident_report.pdf",

            mime="application/pdf"

        )




    # =========================
    # VISUALIZATION
    # =========================


    import plotly.express as px


    st.header(
        "📊 Incident Visualization"
    )



    # ERROR CHART

    st.subheader(
        "🚨 Error Frequency"
    )


    error_chart = (
        df["error_code"]
        .value_counts()
        .reset_index()
    )


    error_chart.columns=[
        "error_code",
        "count"
    ]


    fig1 = px.bar(
        error_chart,
        x="error_code",
        y="count",
        color="error_code"
    )


    st.plotly_chart(
        fig1,
        use_container_width=True
    )



    # APP CHART


    st.subheader(
        "🖥 Application Impact"
    )


    app_chart = (
        df["app_name"]
        .value_counts()
        .reset_index()
    )


    app_chart.columns=[
        "app_name",
        "count"
    ]


    fig2 = px.bar(
        app_chart,
        x="app_name",
        y="count",
        color="app_name"
    )


    st.plotly_chart(
        fig2,
        use_container_width=True
    )



    # TIMELINE


    if "timestamp" in df.columns:


        st.subheader(
            "⏱ Incident Timeline"
        )


        timeline = (
            df.groupby("timestamp")
            .size()
            .reset_index()
        )


        timeline.columns=[
            "timestamp",
            "events"
        ]


        fig3 = px.line(
            timeline,
            x="timestamp",
            y="events",
            markers=True
        )


        st.plotly_chart(
            fig3,
            use_container_width=True
        )



    # SEVERITY


    st.subheader(
        "🔥 Incident Severity"
    )


    count = len(anomalies)



    if count > 5:

        st.error(
            "🔴 HIGH SEVERITY"
        )


    elif count > 2:

        st.warning(
            "🟡 MEDIUM SEVERITY"
        )


    else:

        st.success(
            "🟢 LOW SEVERITY"
        )