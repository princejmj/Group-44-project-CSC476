"""Generate SAMPLE (synthetic) data shaped like the records UI Ventures would hold.
Replace the CSVs in data/ with real exports to run the dashboard on real figures."""
import numpy as np, pandas as pd
rng = np.random.default_rng(476)
months = pd.period_range("2025-01", "2026-10", freq="M")
divs = ["U.I. Hotels", "U&I Fast Food/Bakery", "U.I. Petrol Station", "U.I. Printing Press", "Consultancy/Training"]
base = {"U.I. Hotels": 38e6, "U&I Fast Food/Bakery": 22e6, "U.I. Petrol Station": 55e6, "U.I. Printing Press": 14e6, "Consultancy/Training": 9e6}
# academic-calendar seasonality: peaks around admissions/convocation (Mar, Jul, Nov), dips in Aug-Sep
season = {1:.95,2:.98,3:1.12,4:1.0,5:.97,6:1.0,7:1.1,8:.82,9:.85,10:1.0,11:1.12,12:.9}
rows = []
for m in months:
    for d in divs:
        trend = 1 + 0.012 * (months.get_loc(m))
        rev = base[d] * season[m.month] * trend * rng.normal(1, 0.06)
        rows.append([str(m), d, round(rev, -3), int(rev / rng.uniform(2500, 9000))])
pd.DataFrame(rows, columns=["month", "division", "revenue_ngn", "transactions"]).to_csv("data/sales.csv", index=False)

# hotel bookings
chan = ["Walk-in", "Phone call", "Website form", "Corporate/University", "Third-party listing"]
p = [.34, .22, .06, .30, .08]
b = []
for i in range(3600):
    m = rng.choice(months); c = rng.choice(chan, p=p)
    gt = rng.choice(["Visiting academic/parent", "Corporate", "Conference delegate", "Student-related", "Leisure"], p=[.27,.22,.25,.14,.12])
    nights = int(rng.integers(1, 6)); rate = int(rng.choice([22000, 28000, 35000, 45000], p=[.35,.35,.2,.1]))
    cross = rng.random() < (0.18 if c != "Website form" else 0.30)
    b.append([str(m), c, gt, nights, rate, nights * rate, int(cross)])
pd.DataFrame(b, columns=["month","channel","guest_type","nights","rate_ngn","booking_value_ngn","used_restaurant_or_other_division"]).to_csv("data/hotel_bookings.csv", index=False)

# web + social
w = []
for m in months:
    t = 1 + 0.02 * months.get_loc(m)
    for src, s, cr in [("Google search", 900, .021), ("Facebook", 450, .009), ("Instagram", 380, .011), ("Direct", 700, .026), ("Referral (UI sites)", 260, .018)]:
        ses = int(s * t * rng.normal(1, .1)); w.append([str(m), src, ses, int(ses * cr * rng.normal(1, .15))])
pd.DataFrame(w, columns=["month","source","sessions","reservation_enquiries"]).to_csv("data/web_social.csv", index=False)

# campaigns
c = []
for m in months:
    for ch, sp, ld in [("Facebook posts/ads", 60000, 38), ("Instagram", 45000, 31), ("Flyers/Banners on campus", 90000, 24), ("Radio/Event sponsorship", 150000, 41), ("Email/WhatsApp broadcast", 8000, 29)]:
        c.append([str(m), ch, int(sp * rng.normal(1, .12)), max(1, int(ld * rng.normal(1, .2)))])
pd.DataFrame(c, columns=["month","channel","spend_ngn","leads"]).to_csv("data/campaigns.csv", index=False)

# customer feedback (0-10 recommend score)
f = []
for d, mu in zip(divs, [7.1, 7.4, 6.6, 6.9, 7.8]):
    for _ in range(220):
        f.append([d, int(np.clip(round(rng.normal(mu, 2.0)), 0, 10)), rng.choice(["Staff attitude","Price","Speed","Quality","Awareness of services"], p=[.2,.25,.2,.2,.15])])
pd.DataFrame(f, columns=["division","recommend_score","main_theme"]).to_csv("data/feedback.csv", index=False)
print("sample data written")
