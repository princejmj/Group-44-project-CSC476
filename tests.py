import json, re, os, shutil, subprocess, tempfile, pandas as pd
res = []
def t(name, fn):
    try: ok, note = fn()
    except Exception as e: ok, note = False, str(e)
    res.append((name, "Pass" if ok else "Fail", note)); print(name, "Pass" if ok else "Fail", note)
K = json.load(open("kpis.json"))
files = ["sales", "hotel_bookings", "web_social", "campaigns", "feedback"]
t("T1 All five data files load with no missing values", lambda: (all(pd.read_csv(f"data/{f}.csv").notna().all().all() for f in files), f"{sum(len(pd.read_csv(f'data/{f}.csv')) for f in files)} rows read"))
t("T2 Division revenues reconcile with raw total", lambda: (abs(sum(K["rev_by_div"].values()) - pd.read_csv("data/sales.csv").revenue_ngn.sum()) < 1, "difference below NGN 1"))
def t3():
    w = pd.read_csv("data/web_social.csv").groupby("source")[["sessions", "reservation_enquiries"]].sum()
    return all(abs(w.loc[s, "reservation_enquiries"] / w.loc[s, "sessions"] * 100 - v["cr"]) < 1e-9 for s, v in K["web"].items()), "5 sources recomputed independently"
t("T3 Website conversion rate matches independent recalculation", t3)
t("T4 NPS values lie within -100 and +100", lambda: (all(-100 <= v <= 100 for v in K["nps"].values()), "5 divisions checked"))
def t5():
    h = open("dashboard.html").read(); return h.count("<canvas") == 6 and "const K=" in h and "const D=" in h, f"{h.count('<canvas')} chart canvases found"
t("T5 Dashboard page contains all six charts and embedded KPI data", t5)
def t6():
    d = tempfile.mkdtemp(); shutil.copytree("data", d + "/data"); shutil.copy("build_dashboard.py", d); os.makedirs(d + "/figures")
    s = pd.read_csv(d + "/data/sales.csv"); s["revenue_ngn"] *= 2; s.to_csv(d + "/data/sales.csv", index=False)
    r = subprocess.run(["python3", "build_dashboard.py"], cwd=d, capture_output=True, text=True)
    K2 = json.load(open(d + "/kpis.json")); return r.returncode == 0 and abs(K2["total_revenue"] / K["total_revenue"] - 2) < 1e-9, "doubling revenue input doubled the total output"
t("T6 Dashboard rebuilds correctly when the data files are replaced", t6)
def t7():
    h = open("dashboard.html").read(); D = json.loads(re.search(r"const D=(\{.*?\});\n", h).group(1))
    return abs(sum(sum(v) for v in D["rev"].values()) - K["total_revenue"]) < 1, "filter data reconciles with total revenue"
t("T7 Embedded filter data reconciles with total revenue", t7)
t("T8 Dashboard includes filters, theme toggle and export", lambda: (all(x in open("dashboard.html").read() for x in ['id="from"', 'id="theme"', 'id="csv"']), "controls present"))
json.dump(res, open("test_results.json", "w"))
