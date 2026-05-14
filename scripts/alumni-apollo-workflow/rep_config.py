"""
Rep-specific Apollo email account configuration.
Maps rep names to their Apollo email account IDs.
"""

REP_EMAIL_ACCOUNTS = {
    "Vishwa Srinivasan": "677eb30031d14101b078515e",  # vishwa.srinivasan@astronomer.io
    "Nathan Cooley": "67fd28187ce05b0015aaa132",      # nathan.cooley@astronomer.io
    "Joey Kenney": "688bb3f9219182000d96adb9",        # joey.kenney@astronomer.io
    "Joseph Mason": "65e5e043336f2b01c6622f4b",       # joseph.mason@astronomer.io
    "Victoria Leblanc": "695bfe8d20a642001de49eb4",   # victoria.leblanc@astronomer.io
    "Patrick Healy": "695c0f1747f7840021ca58a7",       # patrick.healy@astronomer.io
    "Wilfred Thomas": "69496d388efa560019dd0618",      # wilfred.thomas@astronomer.io
    "Sean Koljonen": "69495b4615e3f000153a6faa",       # sean.koljonen@astronomer.io
    "Theo Shyne": "69bbd3f3b6c016000d3ac84e",          # theo.shyne@astronomer.io
    "Simon Boepple": "68b596aaea074b001db85382",       # simon.boepple@astronomer.io
}

def get_email_account_id(rep_name: str, default: str = None) -> str:
    """
    Get email account ID for a rep.
    Falls back to default if rep not found.

    Args:
        rep_name: Full name of the rep (e.g., "Nathan Cooley")
        default: Default account ID to use if rep not found

    Returns:
        Email account ID string
    """
    account_id = REP_EMAIL_ACCOUNTS.get(rep_name, default)

    if account_id is None:
        raise ValueError(
            f"No email account found for '{rep_name}'. "
            f"Available reps: {', '.join(REP_EMAIL_ACCOUNTS.keys())}"
        )

    return account_id

def get_email_for_rep(rep_name: str) -> str:
    """
    Get email address for a rep based on their name.

    Args:
        rep_name: Full name of the rep (e.g., "Nathan Cooley")

    Returns:
        Email address string
    """
    # Simple mapping - convert name to email format
    # This is a helper for display purposes
    first, last = rep_name.lower().split(' ', 1)
    return f"{first}.{last}@astronomer.io"
