def protocol_reminders(record: dict, history: list | None = None) -> list[str]:
    reminders = []
    sys_bp = record.get("systolic_bp")
    dia_bp = record.get("diastolic_bp")

    if (sys_bp is not None and sys_bp >= 180) or (dia_bp is not None and dia_bp >= 110):
        reminders.append("BP ≥ 180/110: guideline advises URGENT referral to PHC today.")
    elif (sys_bp is not None and sys_bp >= 140) or (dia_bp is not None and dia_bp >=90):
        reminders.append("BP ≥ 140/90: guideline advises referral to PHC within 1 week.")

    if history and sys_bp is not None:
        prev = [h["systolic"] for h in history if h["systolic"] is not None]
        if len(prev) >= 2 and all(sys_bp > p for p in prev ):
            reminders.append(
                "Systolic BP higher than the last "
                f"{len(prev)} visits — consider follow-up."
            )

    return reminders
