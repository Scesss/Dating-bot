def prioritize_profiles(profiles, current):
    pref = current.get("preference")
    if pref == "Любой":
        return profiles, []
    match = [p for p in profiles if p["gender"] == pref]
    other = [p for p in profiles if p["gender"] != pref]
    return match, other
