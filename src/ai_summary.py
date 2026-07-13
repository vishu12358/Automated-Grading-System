def generate_ai_summary(df: pd.DataFrame) -> str:
    """Generate a structured class performance summary from the grade DataFrame.

    Safely handles empty DataFrames, missing columns, and NaN values.
    All thresholds are consistent with the grading scale used in grade cards.
    """
    # ── Guard: empty or missing data ──────────────────────────────────────
    required = {"Name", "Percentage", "Grade"}
    missing = required - set(df.columns)
    if missing:
        return f"Cannot generate summary — missing columns: {', '.join(sorted(missing))}."

    if df.empty:
        return "No student data available to generate a summary."

    clean = df.dropna(subset=["Percentage", "Grade", "Name"])
    if clean.empty:
        return "All rows contain missing values in key columns. No summary can be generated."

    # ── Core statistics ───────────────────────────────────────────────────
    avg_pct = round(clean["Percentage"].mean(), 2)
    median_pct = round(clean["Percentage"].median(), 2)
    std_pct = round(clean["Percentage"].std(), 2)
    highest = round(clean["Percentage"].max(), 2)
    lowest = round(clean["Percentage"].min(), 2)
    total = len(clean)

    # ── Top performer(s) ──────────────────────────────────────────────────
    top_mask = clean["Percentage"] == highest
    top_students = clean.loc[top_mask, "Name"].tolist()
    top_names = ", ".join(top_students[:3])
    if len(top_students) > 3:
        top_names += f" (+{len(top_students) - 3} more)"

    # ── Weak students (consistent with D/F boundary in grading scale) ──────
    WEAK_THRESHOLD = 50
    weak_count = len(clean[clean["Percentage"] < WEAK_THRESHOLD])
    weak_pct = round((weak_count / total) * 100, 1)

    # ── Grade distribution ────────────────────────────────────────────────
    grade_order = ["A+", "A", "B", "C", "D", "F"]
    grade_dist = clean["Grade"].value_counts()
    most_common = grade_dist.idxmax()
    most_common_count = grade_dist.max()

    # Build ordered distribution string
    dist_parts = []
    for g in grade_order:
        if g in grade_dist.index:
            count = grade_dist[g]
            bar = "█" * count + "░" * (most_common_count - count) if most_common_count else ""
            dist_parts.append(f"  {g:>2}  {bar}  {count}")
    dist_str = "\n".join(dist_parts) if dist_parts else "  No grade data."

    # ── Performance bands ─────────────────────────────────────────────────
    excellent = len(clean[clean["Percentage"] >= 80])
    average = len(clean[(clean["Percentage"] >= 50) & (clean["Percentage"] < 80)])
    below_avg = len(clean[clean["Percentage"] < 50])

    # ── Recommendations (multi-factor) ────────────────────────────────────
    recs = []

    # Weak-student concern
    if weak_pct >= 30:
        recs.append(
            f"CRITICAL: {weak_pct}% of the class ({weak_count}/{total}) "
            f"scored below {WEAK_THRESHOLD}%. Immediate remedial classes "
            f"and one-on-one mentoring are strongly recommended."
        )
    elif weak_pct >= 15:
        recs.append(
            f"WARNING: {weak_count} students ({weak_pct}%) are below "
            f"the {WEAK_THRESHOLD}% threshold. Targeted revision sessions "
            f"for this group would help."
        )

    # Spread / consistency
    if std_pct > 20:
        recs.append(
            f"High variance (σ = {std_pct}) indicates a polarized class — "
            f"some students excel while others struggle significantly. "
            f"Consider differentiated teaching strategies."
        )
    elif std_pct < 5 and total > 5:
        recs.append(
            f"Very low variance (σ = {std_pct}) suggests uniform performance. "
            f"Consider introducing more challenging material to stretch "
            f"top performers."
        )

    # Average-based
    if avg_pct >= 80:
        recs.append(
            "Overall class performance is excellent. Maintain current "
            "teaching methods and introduce advanced problem-solving sessions."
        )
    elif avg_pct >= 65:
        recs.append(
            "Class performance is good but has room for improvement. "
            "Regular mock tests and practice problem sets will help "
            "push average students into the excellent bracket."
        )
    elif avg_pct >= 50:
        recs.append(
            "Class performance is satisfactory but concerning. Conduct "
            "weekly revision sessions and provide structured study guides."
        )
    else:
        recs.append(
            "Class performance is critically low. A comprehensive "
            "reteaching strategy is needed — consider splitting the "
            "class into ability groups for focused intervention."
        )

    # Gap between top and bottom
    gap = highest - lowest
    if gap > 40 and total > 3:
        recs.append(
            f"Large performance gap of {gap:.1f} percentage points "
            f"between highest ({highest}%) and lowest ({lowest}%). "
            f"Peer tutoring programs may be effective."
        )

    if not recs:
        recs.append("No specific recommendations at this time.")

    # ── Assemble summary ──────────────────────────────────────────────────
    summary = f"""
╔══════════════════════════════════════════════════════════╗
║              CLASS PERFORMANCE SUMMARY                   ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Total Students       :  {total:<34}║
║  Average Percentage   :  {avg_pct:<34}║
║  Median Percentage    :  {median_pct:<34}║
║  Standard Deviation   :  {std_pct:<34}║
║  Highest Score        :  {highest:<34}║
║  Lowest Score         :  {lowest:<34}║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║  TOP PERFORMER(S)                                        ║
╠══════════════════════════════════════════════════════════╣
║  {top_names:<54}║
║  Score: {highest}%{' ' * (46 - len(str(highest)))}║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║  GRADE DISTRIBUTION           (Most Common: {most_common})  ║
╠══════════════════════════════════════════════════════════╣
║{dist_str:<58}║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║  PERFORMANCE BANDS                                      ║
╠══════════════════════════════════════════════════════════╣
║  Excellent (≥80%)    :  {excellent:<28}║
║  Average  (50–79%)   :  {average:<28}║
║  Below Avg (<50%)    :  {below_avg:<28}║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║  WEAK STUDENTS  (Below {WEAK_THRESHOLD}%)                          ║
╠══════════════════════════════════════════════════════════╣
║  Count: {weak_count:<3}  ({weak_pct}% of class){' ' * (26 - len(str(weak_pct)))}║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║  RECOMMENDATIONS                                         ║
╠══════════════════════════════════════════════════════════╣"""

    for i, rec in enumerate(recs, 1):
        wrapped = _wrap_fixed(rec, width=52)
        for j, line in enumerate(wrapped):
            prefix = f"  {i}." if j == 0 else "    "
            summary += f"\n║{prefix} {line:<52}║"

    summary += f"""
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """.strip()

    return summary


def _wrap_fixed(text: str, width: int) -> list[str]:
    """Word-wrap text to a fixed width, returning a list of lines."""
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if len(test) <= width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            # Handle single words longer than width
            if len(word) > width:
                lines.append(word[:width])
                word = word[width:]
                while word:
                    lines.append(word[:width])
                    word = word[width:]
                current = []
            else:
                current = [word]
    if current:
        lines.append(" ".join(current))
    return lines