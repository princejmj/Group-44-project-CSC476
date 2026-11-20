"""Reads CSVs in data/, computes marketing KPIs, saves figures and a self-contained dashboard.html"""
import json, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

S = pd.read_csv("data/sales.csv"); H = pd.read_csv("data/hotel_bookings.csv")
W = pd.read_csv("data/web_social.csv"); C = pd.read_csv("data/campaigns.csv"); F = pd.read_csv("data/feedback.csv")

K = {}
K["total_revenue"] = float(S.revenue_ngn.sum())
rev_div = S.groupby("division").revenue_ngn.sum().sort_values(ascending=False)
K["rev_by_div"] = {k: float(v) for k, v in rev_div.items()}
mon = S.groupby("month").revenue_ngn.sum()
K["monthly_rev"] = {k: float(v) for k, v in mon.items()}
byname = S.assign(m=S.month.str[-2:].astype(int)).groupby("m").revenue_ngn.mean()
K["peak_month"], K["low_month"] = int(byname.idxmax()), int(byname.idxmin())
K["season_gap_pct"] = float((byname.max() / byname.min() - 1) * 100)
hc = H.groupby("channel").agg(bookings=("nights", "size"), value=("booking_value_ngn", "mean"), cross=("used_restaurant_or_other_division", "mean"))
K["hotel_channels"] = {k: {"bookings": int(r.bookings), "avg_value": float(r.value), "cross_rate": float(r.cross)} for k, r in hc.iterrows()}
wc = W.groupby("source").agg(sessions=("sessions", "sum"), enq=("reservation_enquiries", "sum"))
wc["cr"] = wc.enq / wc.sessions * 100
K["web"] = {k: {"sessions": int(r.sessions), "enq": int(r.enq), "cr": float(r.cr)} for k, r in wc.iterrows()}
cc = C.groupby("channel").agg(spend=("spend_ngn", "sum"), leads=("leads", "sum")); cc["cpl"] = cc.spend / cc.leads
K["campaign"] = {k: {"spend": float(r.spend), "leads": int(r.leads), "cpl": float(r.cpl)} for k, r in cc.iterrows()}
def nps(x): return float(((x >= 9).mean() - (x <= 6).mean()) * 100)
K["nps"] = {d: nps(g.recommend_score) for d, g in F.groupby("division")}
K["web_total_sessions"] = int(W.sessions.sum()); K["web_total_enq"] = int(W.reservation_enquiries.sum())
K["web_share_hotel_bookings_pct"] = float((H.channel == "Website form").mean() * 100)
K["cross_rate_overall"] = float(H.used_restaurant_or_other_division.mean() * 100)
piv = S.pivot_table(index="month", columns="division", values="revenue_ngn", aggfunc="sum").fillna(0)
D = {"months": list(piv.index), "divs": list(piv.columns), "rev": {d: [float(v) for v in piv[d]] for d in piv.columns}}
json.dump(K, open("kpis.json", "w"), indent=1)

col = ["#1f4e79", "#2e75b6", "#9dc3e6", "#c55a11", "#7f7f7f"]
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
def save(n): plt.tight_layout(); plt.savefig(f"figures/{n}.png", dpi=170); plt.close()

fig, ax = plt.subplots(figsize=(6.4, 3.2)); ax.barh(list(rev_div.index)[::-1], rev_div.values[::-1] / 1e6, color=col[1]); ax.set_xlabel("Revenue (NGN million), Jan 2025 to Oct 2026 (sample data)"); save("fig_rev_div")
fig, ax = plt.subplots(figsize=(6.6, 3.2)); ax.plot(range(len(mon)), mon.values / 1e6, color=col[0], marker="o", ms=3); ax.set_xticks(range(0, len(mon), 3)); ax.set_xticklabels(list(mon.index)[::3], rotation=30); ax.set_ylabel("NGN million"); save("fig_monthly")
fig, ax = plt.subplots(figsize=(6.2, 3.2)); ax.bar(hc.index, hc.bookings, color=col[1]); ax.set_ylabel("Bookings"); plt.xticks(rotation=18, ha="right"); save("fig_channels")
fig, ax = plt.subplots(figsize=(6.2, 3.2)); ax.bar(wc.index, wc.cr, color=col[3]); ax.set_ylabel("Enquiry conversion (%)"); plt.xticks(rotation=18, ha="right"); save("fig_web_cr")
fig, ax = plt.subplots(figsize=(6.2, 3.2)); ax.bar(cc.index, cc.cpl, color=col[0]); ax.set_ylabel("Cost per lead (NGN)"); plt.xticks(rotation=18, ha="right"); save("fig_cpl")
fig, ax = plt.subplots(figsize=(6.2, 3.2)); n = pd.Series(K["nps"]); ax.bar(n.index, n.values, color=col[2]); ax.axhline(0, color="k", lw=.6); ax.set_ylabel("NPS"); plt.xticks(rotation=18, ha="right"); save("fig_nps")

# architecture diagram
from matplotlib.patches import FancyBboxPatch
fig, ax = plt.subplots(figsize=(7.2, 3.6)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 5)
def box(x, y, w, h, t, c):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=c, ec="#1f4e79")); ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7.5)
box(0.1, 3.4, 2.2, 1.2, "Data sources\nPOS/sales records\nHotel bookings\nWeb & social stats", "#deebf7")
box(0.1, 1.4, 2.2, 1.2, "Customer feedback\nSurveys (0-10 score)\nCampaign records", "#deebf7")
box(3.2, 2.3, 2.3, 1.6, "Data layer\nCSV import, cleaning,\nvalidation (pandas)", "#fff2cc")
box(6.1, 2.3, 2.0, 1.6, "Analytics engine\nKPIs, seasonality,\nchannel & NPS analysis", "#e2f0d9")
box(8.55, 2.5, 1.35, 1.2, "Dashboard\n(HTML)", "#fbe5d6")
box(5.6, 0.3, 4.3, 1.1, "Marketing decisions:\ncampaign timing, budget, cross-selling", "#ededed")
for a, b in [((2.3, 4.0), (3.2, 3.3)), ((2.3, 2.0), (3.2, 2.9)), ((5.5, 3.1), (6.1, 3.1)), ((8.1, 3.1), (8.55, 3.1)), ((9.2, 2.5), (8.8, 1.4))]:
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", color="#1f4e79"))
save("fig_arch")

# dashboard html (plain template, placeholders replaced below, so no brace escaping is needed)
TEMPLATE = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>UI Ventures Marketing Insights Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{--bg:#eef2f7;--card:#fff;--text:#1b2a3a;--muted:#6b7a8d;--brand:#1f4e79;--accent:#c55a11;--grid:#e3e8ef;--shadow:0 4px 14px #1f4e7914}
[data-theme=dark]{--bg:#0e1621;--card:#17222f;--text:#e6edf5;--muted:#93a4b8;--brand:#6fb1ea;--accent:#f0955a;--grid:#2a3848;--shadow:0 4px 14px #0006}
*{box-sizing:border-box}body{font-family:Inter,Segoe UI,Arial,sans-serif;margin:0;background:var(--bg);color:var(--text);transition:background .3s,color .3s}
header{background:linear-gradient(120deg,#12365a,#2e75b6);color:#fff;padding:22px 28px;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between}
h1{font-size:21px;margin:0}header small{opacity:.85}.tools{display:flex;gap:8px;flex-wrap:wrap}
button,select{font:inherit;border-radius:8px;border:1px solid #fff5;padding:7px 12px;cursor:pointer}
header button{background:#ffffff22;color:#fff}header button:hover{background:#ffffff40}
.bar{display:flex;flex-wrap:wrap;gap:12px;align-items:center;padding:14px 28px;position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--grid)}
.bar label{font-size:12px;color:var(--muted);display:flex;flex-direction:column;gap:3px}.bar select{background:var(--card);color:var(--text);border-color:var(--grid)}
.k{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:14px;padding:18px 28px 6px}
.c{background:var(--card);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow);border-top:4px solid var(--brand);font-size:13px;color:var(--muted)}
.c b{display:block;font-size:24px;color:var(--text);margin:4px 0}.up{color:#2e9e5b}.dn{color:#d64545}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;padding:12px 28px}
.p{background:var(--card);border-radius:12px;padding:14px;box-shadow:var(--shadow);animation:in .5s both}.p h3{margin:0 0 10px;font-size:14px}.wide{grid-column:1/-1}
@keyframes in{from{opacity:0;transform:translateY(10px)}}
.i{margin:8px 28px 30px;background:var(--card);border-left:5px solid var(--accent);padding:12px 20px;border-radius:10px;box-shadow:var(--shadow)}.i li{margin:6px 0;line-height:1.45}
footer{text-align:center;color:var(--muted);font-size:12px;padding:0 0 24px}
@media print{.bar,.tools{display:none}body{background:#fff}}
</style></head><body>
<header><div><h1>Marketing Insights Dashboard: UI Ventures Limited</h1><small>CSC 476 Group 44, University of Ibadan. Prototype on simulated sample data</small></div>
<div class="tools"><button id="csv">Export CSV</button><button id="prt">Print / PDF</button><button id="theme">Dark mode</button></div></header>
<div class="bar"><label>From<select id="from"></select></label><label>To<select id="to"></select></label><label>Division<select id="div"></select></label><label>&nbsp;<button id="reset" style="background:var(--card);color:var(--text);border-color:var(--grid)">Reset filters</button></label></div>
<div class="k" id="k"></div><div class="g">
<div class="p wide"><h3>Monthly revenue with 3-month trend projection (NGN m)</h3><canvas id="b" height="90"></canvas></div>
<div class="p"><h3>Revenue by division (NGN m)</h3><canvas id="a"></canvas></div>
<div class="p"><h3>Hotel bookings by channel</h3><canvas id="c"></canvas></div>
<div class="p"><h3>Website enquiry conversion by source (%)</h3><canvas id="d"></canvas></div>
<div class="p"><h3>Cost per lead by campaign channel (NGN)</h3><canvas id="e"></canvas></div>
<div class="p"><h3>Net Promoter Score by division</h3><canvas id="f"></canvas></div></div>
<div class="i"><b>Auto-generated insights</b><ul id="ins"></ul></div>
<footer>Filters apply to revenue figures. Website, campaign, hotel and NPS figures cover the full dataset.</footer>
<script>const K=__K__;
const D=__D__;
const $=id=>document.getElementById(id),M=D.months,DV=D.divs,n=x=>x.toLocaleString(undefined,{maximumFractionDigits:0});
const PAL=['#1f4e79','#2e75b6','#9dc3e6','#c55a11','#7f7f7f'];
M.forEach(m=>{$('from').add(new Option(m,m));$('to').add(new Option(m,m))});
DV.forEach(d=>$('div').add(new Option(d,d)));$('div').add(new Option('All divisions','all'),0);
function reset(){$('from').value=M[0];$('to').value=M[M.length-1];$('div').value='all'}reset();
function nxt(m,k){let[y,mo]=m.split('-').map(Number),o=[];for(let i=0;i<k;i++){mo++;if(mo>12){mo=1;y++}o.push(y+'-'+String(mo).padStart(2,'0'))}return o}
function fc(y,k){const L=y.length;if(L<4)return[];const xm=(L-1)/2,ym=y.reduce((a,b)=>a+b)/L;let sxy=0,sxx=0;y.forEach((v,i)=>{sxy+=(i-xm)*(v-ym);sxx+=(i-xm)**2});const s=sxy/sxx;return Array.from({length:k},(_,j)=>ym+s*(L+j-xm))}
function view(){const a=M.indexOf($('from').value),b=M.indexOf($('to').value),lo=Math.min(a,b),hi=Math.max(a,b),ds=$('div').value==='all'?DV:[$('div').value];
 return{lo,hi,idx:M.slice(lo,hi+1),ds,tot:M.slice(lo,hi+1).map((m,i)=>ds.reduce((s,d)=>s+D.rev[d][lo+i],0))}}
const charts={};
function chart(id,type,labels,data,col,extra){const grid=getComputedStyle(document.documentElement).getPropertyValue('--grid');
 Chart.defaults.color=getComputedStyle(document.documentElement).getPropertyValue('--muted');
 const sets=Array.isArray(data[0])||typeof data[0]==='object'&&data[0]!==null?data:[{data,backgroundColor:col,borderColor:col,borderRadius:5}];
 if(charts[id]){const c=charts[id];c.data.labels=labels;c.data.datasets=sets;['x','y'].forEach(s=>{if(c.options.scales[s])c.options.scales[s].grid.color=grid});c.update();return}
 charts[id]=new Chart($(id),{type,data:{labels,datasets:sets},options:Object.assign({plugins:{legend:{display:sets.length>1||type==='doughnut'}},animation:{duration:700},
  scales:type==='doughnut'?{}:{x:{grid:{color:grid}},y:{grid:{color:grid}}}},extra||{})})}
function count(el,to,fmt){const t0=performance.now();(function f(t){const p=Math.min(1,(t-t0)/600);el.textContent=fmt(to*p);if(p<1)requestAnimationFrame(f)})(t0)}
function render(){const v=view(),tot=v.tot.reduce((a,b)=>a+b,0),avg=tot/v.tot.length,L=v.tot.length,
 mom=L>1?(v.tot[L-1]/v.tot[L-2]-1)*100:null;
 const cards=[['Revenue in selection',tot,x=>'NGN '+(x/1e9).toFixed(2)+' bn','across '+L+' month(s)'],['Average per month',avg,x=>'NGN '+(x/1e6).toFixed(1)+' m',v.ds.length>1?'all divisions':v.ds[0]],
 ['Latest month vs previous',mom,x=>(x>=0?'+':'')+x.toFixed(1)+'%',mom===null?'need 2+ months':'month on month'],['Seasonal swing',K.season_gap_pct,x=>x.toFixed(0)+'%','peak vs low month'],
 ['Website share of bookings',K.web_share_hotel_bookings_pct,x=>x.toFixed(1)+'%','online booking uptake'],['Guests using a 2nd division',K.cross_rate_overall,x=>x.toFixed(1)+'%','cross-selling rate']];
 $('k').innerHTML=cards.map((c,i)=>'<div class="c">'+c[0]+'<b id="kv'+i+'"></b><span class="'+(i==2&&c[1]!==null?(c[1]>=0?'up':'dn'):'')+'">'+c[3]+'</span></div>').join('');
 cards.forEach((c,i)=>c[1]===null?$('kv'+i).textContent='n/a':count($('kv'+i),c[1],c[2]));
 const f=fc(v.tot,3),fl=nxt(v.idx[L-1],f.length),m6=x=>x/1e6;
 chart('b','line',v.idx.concat(fl),[{label:'Actual',data:v.tot.map(m6).concat(f.map(()=>null)),borderColor:PAL[0],backgroundColor:'#2e75b633',fill:true,tension:.3,pointRadius:2},
  {label:'Trend projection',data:v.tot.map((x,i)=>i==L-1?m6(x):null).concat(f.map(m6)),borderColor:PAL[3],borderDash:[6,5],tension:.3,pointRadius:3}]);
 const dv=DV.map(d=>D.rev[d].slice(v.lo,v.hi+1).reduce((a,b)=>a+b,0)/1e6);
 chart('a','doughnut',DV,[{data:dv,backgroundColor:PAL.concat(['#548235']),borderWidth:0}],null,{cutout:'60%'});
 const top=DV[dv.indexOf(Math.max(...dv))],bi=v.tot.indexOf(Math.max(...v.tot)),wi=v.tot.indexOf(Math.min(...v.tot));
 const web=Object.keys(K.web),cmp=Object.keys(K.campaign),best=web.reduce((a,b)=>K.web[a].cr>K.web[b].cr?a:b),cheap=cmp.reduce((a,b)=>K.campaign[a].cpl<K.campaign[b].cpl?a:b),dear=cmp.reduce((a,b)=>K.campaign[a].cpl>K.campaign[b].cpl?a:b);
 const nl=Object.keys(K.nps),lowN=nl.reduce((a,b)=>K.nps[a]<K.nps[b]?a:b);
 $('ins').innerHTML=['In the selected period '+top+' earns the most ('+(Math.max(...dv)/dv.reduce((a,b)=>a+b)*100).toFixed(0)+'% of revenue). Best month: '+v.idx[bi]+' (NGN '+n(v.tot[bi]/1e6)+' m); weakest: '+v.idx[wi]+' (NGN '+n(v.tot[wi]/1e6)+' m).',
 'Revenue is seasonal: months '+K.peak_month+' and '+K.low_month+' (peak vs low) differ by about '+K.season_gap_pct.toFixed(0)+'%, so promotions should be timed ahead of low months.',
 'Highest website conversion: '+best+' ('+K.web[best].cr.toFixed(1)+'%). Lowest cost per lead: '+cheap+' (NGN '+n(K.campaign[cheap].cpl)+'); highest: '+dear+' (NGN '+n(K.campaign[dear].cpl)+'). Shift budget toward '+cheap+'.',
 'Only '+K.web_share_hotel_bookings_pct.toFixed(1)+'% of hotel bookings use the website form, so online booking is under-used.',
 'Lowest customer advocacy: '+lowN+' (NPS '+K.nps[lowN].toFixed(0)+'). Prioritise service improvements there.'].map(t=>'<li>'+t+'</li>').join('')}
const hc=Object.keys(K.hotel_channels),wl=Object.keys(K.web),cl=Object.keys(K.campaign),nl=Object.keys(K.nps);
function static_(){chart('c','bar',hc,hc.map(k=>K.hotel_channels[k].bookings),PAL[1]);chart('d','bar',wl,wl.map(k=>K.web[k].cr),PAL[3]);chart('e','bar',cl,cl.map(k=>K.campaign[k].cpl),PAL[0]);
 chart('f','bar',nl,nl.map(k=>K.nps[k]),nl.map(k=>K.nps[k]>=0?'#2e9e5b':'#d64545'))}
function all(){render();static_()}
['from','to','div'].forEach(i=>$(i).onchange=render);$('reset').onclick=()=>{reset();render()};
$('theme').onclick=()=>{const d=document.documentElement.dataset.theme==='dark';document.documentElement.dataset.theme=d?'light':'dark';$('theme').textContent=d?'Dark mode':'Light mode';try{localStorage.setItem('uiv-theme',d?'light':'dark')}catch(e){}all()};
try{if(localStorage.getItem('uiv-theme')==='dark'){document.documentElement.dataset.theme='dark';$('theme').textContent='Light mode'}}catch(e){}
$('prt').onclick=()=>window.print();
$('csv').onclick=()=>{const v=view(),rows=['month,revenue_ngn'].concat(v.idx.map((m,i)=>m+','+v.tot[i]));const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([rows.join('\n')],{type:'text/csv'}));a.download='revenue_selection.csv';a.click()};
all();
</script></body></html>"""
html = TEMPLATE.replace("__K__", json.dumps(K)).replace("__D__", json.dumps(D))
open("dashboard.html", "w").write(html)
open("index.html", "w").write(html)
print(json.dumps({k: K[k] for k in ["total_revenue","peak_month","low_month","season_gap_pct","web_share_hotel_bookings_pct","cross_rate_overall"]}, indent=1))
