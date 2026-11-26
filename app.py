import pandas as pd
import streamlit as st

st.set_page_config(page_title="Student Grade Calculator", page_icon="🎓", layout="wide")

COLS = ["Assignment", "Quiz", "Midterm", "Final exam"]


def letter(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "E"


st.title("🎓 Student Grade Calculator")
st.caption("Enter each subject's scores. The app applies your weights, then shows the final score, letter grade, and pass status.")

# ---- Sidebar: student info and weights ----
with st.sidebar:
    st.header("Settings")
    student = st.text_input("Student name", placeholder="e.g. Rina Putri")
    kkm = st.number_input("Passing mark (KKM)", min_value=0, max_value=100, value=75)
    st.subheader("Score weights (%)")
    weights = [
        st.number_input(c, min_value=0, max_value=100, value=v, key=f"w_{c}")
        for c, v in zip(COLS, [20, 20, 25, 35])
    ]
    total = sum(weights)
    if total == 100:
        st.success("Total weight: 100% ✓")
    else:
        st.error(f"Total weight is {total}%. It must equal 100%.")
    st.caption("Scale: A 90–100 · B 80–89 · C 70–79 · D 60–69 · E below 60")

# ---- Subject table (editable, rows can be added or deleted) ----
st.subheader("Subjects")
default = pd.DataFrame(
    {
        "Subject": ["Mathematics", "English", "Science"],
        **{c: [None, None, None] for c in COLS},
    }
)
edited = st.data_editor(
    default,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        c: st.column_config.NumberColumn(c, min_value=0, max_value=100, step=0.5)
        for c in COLS
    },
    key="subjects",
)

if st.button("Calculate grades", type="primary"):
    if total != 100:
        st.error("Fix the weights first: they must add up to exactly 100%.")
        st.stop()

    rows, skipped = [], 0
    for _, r in edited.iterrows():
        name = str(r["Subject"]).strip() if pd.notna(r["Subject"]) else ""
        scores = [r[c] for c in COLS]
        if not name or any(pd.isna(s) for s in scores):
            skipped += 1
            continue
        final = round(sum(s * w / 100 for s, w in zip(scores, weights)), 1)
        rows.append(
            {
                "Subject": name,
                "Final score": final,
                "Grade": letter(final),
                "Status": "Passed" if final >= kkm else "Remedial",
            }
        )

    if skipped:
        st.warning(f"{skipped} row(s) skipped because the subject name or a score is missing.")
    if not rows:
        st.info("Add at least one subject with all four scores.")
        st.stop()

    result = pd.DataFrame(rows)
    avg = result["Final score"].mean()
    best = result.loc[result["Final score"].idxmax()]
    low = result.loc[result["Final score"].idxmin()]
    remedial = result[result["Status"] == "Remedial"]["Subject"].tolist()

    st.subheader(f"Report: {student.strip() or 'The student'}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average", f"{avg:.1f}", letter(avg))
    c2.metric("Highest", f"{best['Final score']:.1f}", best["Subject"])
    c3.metric("Lowest", f"{low['Final score']:.1f}", low["Subject"])
    c4.metric("Remedial subjects", len(remedial))

    st.dataframe(result, use_container_width=True, hide_index=True)
    st.bar_chart(result.set_index("Subject")["Final score"])

    if remedial:
        st.error("Needs remedial work in: " + ", ".join(remedial))
    else:
        st.success("All subjects are at or above the passing mark.")

    st.download_button(
        "Download report (CSV)",
        result.to_csv(index=False).encode("utf-8"),
        file_name="grade_report.csv",
        mime="text/csv",
    )
