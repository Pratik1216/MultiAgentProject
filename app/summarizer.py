def summarize(rows, metrics):
    if not rows:
        return "No data available for the selected period."


    summaries = []
    for m in metrics:
        values = [r[m] for r in rows]
        delta = values[-1] - values[0]
        if delta > 0:
            summaries.append(f"{m} increased over the period.")
        elif delta < 0:
            summaries.append(f"{m} decreased slightly over the period.")
        else:
            summaries.append(f"{m} remained stable over the period.")

    return " ".join(summaries)