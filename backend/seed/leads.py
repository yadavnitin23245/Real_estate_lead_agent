"""Sample leads so the sales inbox and metrics aren't empty on first run.

All names, emails and phone numbers are fictional (example.com, 90000 xxxxx).
"""

from __future__ import annotations

from dataclasses import dataclass, field

L = 100_000  # one lakh
CR = 10_000_000  # one crore


@dataclass
class LeadSeed:
    name: str
    email: str
    phone: str
    status: str
    days_ago: int
    first_message: str
    city: str | None = "Pune"
    localities: list[str] = field(default_factory=list)
    property_type: str | None = None
    bedrooms: int | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    timeline_months: int | None = None
    loan_preapproved: bool | None = None
    must_haves: dict[str, bool] = field(default_factory=dict)
    soft_preferences: str | None = None
    notes: str | None = None
    visit: tuple[str, str] | None = None  # (preferred_time, status)
    # Full custom chat for non-English leads; otherwise a generic one is generated.
    chat: list[tuple[str, str]] | None = None


LEADS: list[LeadSeed] = [
    LeadSeed("Aarav Mehta", "aarav.mehta@example.com", "+91 90000 10001", "handed_off", 0,
             "Looking for a 3 BHK in Baner or Aundh, somewhere quiet and close to a good school.",
             localities=["Baner", "Aundh"], property_type="apartment", bedrooms=3,
             budget_min=120 * L, budget_max=160 * L, timeline_months=2, loan_preapproved=True,
             must_haves={"near_school": True}, soft_preferences="quiet lane, near a good school",
             visit=("Saturday 11 am", "requested")),
    LeadSeed("Sneha Iyer", "sneha.iyer@example.com", "+91 90000 10002", "handed_off", 0,
             "We both work in Hinjewadi. Need a 2 BHK in Hinjewadi or Wakad with a short commute.",
             localities=["Hinjewadi", "Wakad"], property_type="apartment", bedrooms=2,
             budget_min=65 * L, budget_max=85 * L, timeline_months=3, loan_preapproved=True,
             must_haves={"has_parking": True}, soft_preferences="short commute to the IT park, gated society",
             visit=("Sunday morning", "confirmed")),
    LeadSeed("Rahul Sharma", "rahul.sharma@example.com", "+91 90000 10003", "handed_off", 1,
             "Hi, I want a 2 BHK near Kharadi or Viman Nagar.",
             localities=["Kharadi", "Viman Nagar"], property_type="apartment", bedrooms=2,
             budget_min=90 * L, budget_max=120 * L, timeline_months=5, loan_preapproved=False,
             soft_preferences="close to the airport, lively area with cafes"),
    LeadSeed("Pooja Nair", "pooja.nair@example.com", "+91 90000 10004", "handed_off", 2,
             "Kothrud mein 2 BHK chahiye, metro ke paas ho toh best.",
             localities=["Kothrud"], property_type="apartment", bedrooms=2,
             budget_min=100 * L, budget_max=130 * L, timeline_months=6, loan_preapproved=None,
             must_haves={"near_metro": True}, soft_preferences="metro ke paas, shaant society",
             chat=[
                 ("user", "Kothrud mein 2 BHK chahiye, metro ke paas ho toh best."),
                 ("assistant", "Zaroor! Aapka budget kitna hai?"),
                 ("user", "1 se 1.3 crore tak."),
                 ("assistant", "Theek hai. Aap kab tak lena chahte hain?"),
                 ("user", "Agle 6 mahine mein."),
                 ("assistant", "Kothrud mein metro ke paas 3 achhe options mile hain. Maine aapki details "
                               "hamare agent ko de di hain, woh aapko jaldi call karenge."),
             ]),
    LeadSeed("Karan Malhotra", "karan.malhotra@example.com", "+91 90000 10005", "handed_off", 3,
             "Interested in a villa in Bavdhan with hill views.",
             localities=["Bavdhan"], property_type="villa", bedrooms=4,
             budget_min=300 * L, budget_max=450 * L, timeline_months=4, loan_preapproved=True,
             soft_preferences="hill view, green and peaceful, private garden"),
    LeadSeed("Neha Gupta", "neha.gupta@example.com", "+91 90000 10006", "nurture", 4,
             "Magarpatta ya Hadapsar mein 3 BHK, shaant area ho toh better. Abhi jaldi nahi hai.",
             localities=["Magarpatta", "Hadapsar"], property_type="apartment", bedrooms=3,
             budget_min=100 * L, budget_max=130 * L, timeline_months=12, loan_preapproved=False,
             soft_preferences="shaant area, township",
             chat=[
                 ("user", "Magarpatta ya Hadapsar mein 3 BHK, shaant area ho toh better. Abhi jaldi nahi hai."),
                 ("assistant", "Bilkul. Budget kitna soch rahe hain?"),
                 ("user", "1 se 1.3 Cr."),
                 ("assistant", "Aur kab tak kharidna hai? Loan pre-approved hai?"),
                 ("user", "Shayad ek saal mein. Loan abhi nahi liya."),
                 ("assistant", "Samajh gaya. Kuch matching options mile hain. Kya main yeh aapko email kar doon "
                               "taaki aap aaram se dekh sakein?"),
             ]),
    LeadSeed("Amit Kulkarni", "amit.kulkarni@example.com", "+91 90000 10007", "nurture", 6,
             "मुझे हिंजवडी में निवेश के लिए एक प्लॉट चाहिए।",
             localities=["Hinjewadi"], property_type="plot_land",
             budget_min=50 * L, budget_max=80 * L, timeline_months=18,
             soft_preferences="निवेश के लिए, गेटेड लेआउट",
             chat=[
                 ("user", "मुझे हिंजवडी में निवेश के लिए एक प्लॉट चाहिए।"),
                 ("assistant", "ज़रूर! आपका बजट कितना है?"),
                 ("user", "50 से 80 लाख।"),
                 ("assistant", "आप कब तक खरीदना चाहते हैं?"),
                 ("user", "डेढ़ साल में, कोई जल्दी नहीं है।"),
                 ("assistant", "ठीक है। मैंने कुछ प्लॉट ढूंढे हैं। क्या मैं ये विकल्प आपको ईमेल कर दूँ?"),
             ]),
    LeadSeed("Divya Reddy", "divya.reddy@example.com", "+91 90000 10008", "qualifying", 1,
             "Hi! Any 2 BHK options in Pimple Saudagar?",
             localities=["Pimple Saudagar"], property_type="apartment", bedrooms=2,
             budget_min=70 * L, budget_max=90 * L),
    LeadSeed("Siddharth Rao", "siddharth.rao@example.com", "+91 90000 10009", "closed", 9,
             "Need office space in Viman Nagar for my firm, around 1,000 sq ft.",
             localities=["Viman Nagar"], property_type="commercial",
             budget_min=100 * L, budget_max=200 * L, timeline_months=3, loan_preapproved=True,
             soft_preferences="main road visibility, ready fit-out",
             notes="Visited 2 units. Closed on the Nagar Road office.",
             visit=("Weekday 4 pm", "completed")),
    LeadSeed("Meera Joshi", "meera.joshi@example.com", "+91 90000 10010", "new", 0,
             "Hello, just browsing for now.", localities=[]),
    LeadSeed("Farhan Shaikh", "farhan.shaikh@example.com", "+91 90000 10011", "new", 0,
             "Do you have 2 BHK flats?", property_type="apartment", bedrooms=2),
    LeadSeed("Kavya Menon", "kavya.menon@example.com", "+91 90000 10012", "qualifying", 2,
             "Looking for a 1 BHK in Wakad to rent out.",
             localities=["Wakad"], property_type="apartment", bedrooms=1,
             budget_min=45 * L, budget_max=60 * L, timeline_months=3,
             soft_preferences="good rental demand"),
    LeadSeed("Arjun Singh", "arjun.singh@example.com", "+91 90000 10013", "qualifying", 3,
             "Want an independent house in Baner or Aundh with a garden.",
             localities=["Baner", "Aundh"], property_type="house", bedrooms=3,
             budget_max=300 * L, soft_preferences="garden, quiet street"),
    LeadSeed("Ishita Banerjee", "ishita.banerjee@example.com", "+91 90000 10014", "nurture", 5,
             "2 BHK in Kharadi, park facing if possible.",
             localities=["Kharadi"], property_type="apartment", bedrooms=2,
             budget_min=80 * L, budget_max=100 * L, timeline_months=9, loan_preapproved=False,
             soft_preferences="park facing"),
    LeadSeed("Manish Agarwal", "manish.agarwal@example.com", "+91 90000 10015", "handed_off", 1,
             "We need a 4 BHK in Aundh or Baner for my parents and us. Ready to move.",
             localities=["Aundh", "Baner"], property_type="apartment", bedrooms=4,
             budget_min=220 * L, budget_max=300 * L, timeline_months=1, loan_preapproved=True,
             soft_preferences="big family, lift, peaceful society",
             visit=("Weekday evening after 6 pm", "requested")),
]


def generic_chat(lead: LeadSeed, agent_name: str | None, match_count: int) -> list[tuple[str, str]]:
    """A short plausible English chat built from the lead's profile."""
    from app.formatting import format_budget, format_timeline

    msgs: list[tuple[str, str]] = [("user", lead.first_message)]
    if lead.budget_min or lead.budget_max:
        msgs += [("assistant", "Happy to help! What budget range are you working with?"),
                 ("user", f"Around {format_budget(lead.budget_min, lead.budget_max)}.")]
    else:
        msgs.append(("assistant", "Happy to help! Which area of Pune are you looking in, and what's your budget?"))
        return msgs
    if lead.timeline_months is not None:
        loan = ""
        if lead.loan_preapproved is True:
            loan = " Our home loan is already pre-approved."
        elif lead.loan_preapproved is False:
            loan = " We haven't applied for a loan yet."
        msgs += [("assistant", "Thanks! When are you planning to buy, and is your home loan pre-approved?"),
                 ("user", f"{format_timeline(lead.timeline_months).capitalize()}.{loan}")]
    else:
        msgs.append(("assistant", "Got it. When are you planning to buy?"))
        return msgs
    if lead.status in {"handed_off", "closed"} and agent_name:
        msgs.append(("assistant", f"I found {match_count} strong matches for you. I've shared your requirements "
                                  f"with {agent_name}, who will call you shortly."))
    elif lead.status == "nurture":
        msgs.append(("assistant", f"I found {match_count} options that fit. Would you like me to email them "
                                  f"so you can review them at your own pace?"))
    elif lead.loan_preapproved is None:
        msgs.append(("assistant", "Great. Is your home loan pre-approved, or will you be applying for one?"))
    return msgs
