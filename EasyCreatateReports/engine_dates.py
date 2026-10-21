import datetime

def get_current_greek_month():
    """Επιστρέφει τον τρέχοντα μήνα στα ελλην γενική πτώση (π.χ. Οκτωβρίου)."""
    gr_months = {
        1: "ΙΑΝΟΥΑΡΙΟΣ", 2: "ΦΕΒΡΟΥΑΡΙΟΣ", 3: "ΜΑΡΤΙΟΣ", 4: "ΑΠΡΙΛΙΟΣ",
        5: "ΜΑΪΟΣ", 6: "ΙΟΥΝΙΟΣ", 7: "ΙΟΥΛΙΟΣ", 8: "ΑΥΓΟΥΣΤΟΣ",
        9: "ΣΕΠΤΕΜΒΡΙΟΣ", 10: "ΟΚΤΩΒΡΙΟΣ", 11: "ΝΟΕΜΒΡΙΟΣ", 12: "ΔΕΚΕΜΒΡΙΟΣ"
    }
    now = datetime.datetime.now()
    return gr_months.get(now.month, "")

# Ένα λεξικό με έτοιμες μεταβλητές ημερομηνίας που θα περνάνε στον engine
def get_dates_env():
    now = datetime.datetime.now()
    return {
        "Month": get_current_greek_month(),
        "Year": str(now.year),
        "Day": str(now.day),
        "DateNow": now.strftime("%d/%m/%Y")
    }
