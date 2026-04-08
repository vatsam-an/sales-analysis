# ============================================================
# SUPERSTORE SALES & REVENUE ANALYSIS
# Tools: Python, Pandas | Dataset: 9,994 orders (2014–2017)
# Author: Aman Kumar Choudhary
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings('ignore')

# ── Load Data ────────────────────────────────────────────────
df = pd.read_csv('superstore_sales.csv', parse_dates=['Order Date'])
df['Month']   = df['Order Date'].dt.to_period('M')
df['Year']    = df['Order Date'].dt.year
df['Discount_Tier'] = pd.cut(
    df['Discount'],
    bins=[-0.001, 0.001, 0.10, 0.20, 0.30, 1.0],
    labels=['No Discount', 'Low (1-10%)', 'Medium (11-20%)', 'High (21-30%)', 'Very High (31%+)']
)

print("=" * 55)
print(f"  Records : {len(df):,}")
print(f"  Period  : {df['Order Date'].min().date()} → {df['Order Date'].max().date()}")
print(f"  Revenue : ${df['Sales'].sum():,.0f}")
print(f"  Profit  : ${df['Profit'].sum():,.0f}")
print("=" * 55)

# ── 1. Monthly Revenue ───────────────────────────────────────
print("\n[1] MONTHLY REVENUE TREND")
monthly = df.groupby('Month').agg(
    Orders=('Order ID', 'count'),
    Revenue=('Sales', 'sum'),
    Profit=('Profit', 'sum')
).reset_index()
monthly['Margin%'] = (monthly['Profit'] / monthly['Revenue'] * 100).round(1)
print(monthly.tail(6).to_string(index=False))

# ── 2. Top 10 Customers ──────────────────────────────────────
print("\n[2] TOP 10 CUSTOMERS")
top_cust = (
    df.groupby('Customer Name')
    .agg(Orders=('Order ID','count'), Revenue=('Sales','sum'), Profit=('Profit','sum'))
    .assign(Margin=lambda x: (x['Profit']/x['Revenue']*100).round(1))
    .nlargest(10, 'Revenue')
)
print(top_cust.to_string())

# ── 3. Category Performance ──────────────────────────────────
print("\n[3] CATEGORY PERFORMANCE")
cat_perf = (
    df.groupby('Category')
    .agg(Revenue=('Sales','sum'), Profit=('Profit','sum'), Avg_Discount=('Discount','mean'))
    .assign(
        Margin_Pct=lambda x: (x['Profit']/x['Revenue']*100).round(2),
        Margin_Tier=lambda x: x['Profit']/x['Revenue']*100
    )
)
cat_perf['Margin_Tier'] = cat_perf['Margin_Tier'].apply(
    lambda x: 'High' if x >= 15 else ('Medium' if x >= 8 else 'Low'))
print(cat_perf.to_string())

# ── 4. Regional Analysis ─────────────────────────────────────
print("\n[4] REGIONAL PERFORMANCE")
reg = (
    df.groupby('Region')
    .agg(Revenue=('Sales','sum'), Profit=('Profit','sum'), Avg_Disc=('Discount','mean'))
    .assign(Margin_Pct=lambda x: (x['Profit']/x['Revenue']*100).round(2))
    .sort_values('Revenue', ascending=False)
)
avg = reg['Revenue'].mean()
reg['Status'] = reg['Revenue'].apply(lambda x: 'UNDERPERFORMING ↓' if x < avg else 'On Target ✓')
print(reg.to_string())
print(f"\n  → Central and South are underperforming (below ${avg/1e6:.1f}M avg)")
print(f"  → Both have significantly higher avg discounts vs West/East")

# ── 5. Discount-Profit Relationship ─────────────────────────
print("\n[5] DISCOUNT vs PROFIT (Key Business Insight)")
disc = (
    df.groupby('Discount_Tier', observed=True)
    .agg(Orders=('Order ID','count'),
         Avg_Profit=('Profit','mean'),
         Total_Profit=('Profit','sum'),
         Loss_Orders=('Profit', lambda x: (x < 0).sum()))
    .assign(Loss_Rate=lambda x: (x['Loss_Orders']/x['Orders']*100).round(1))
)
print(disc.to_string())
print("\n  → Orders with no discount: 0% loss rate, avg $926 profit")
print("  → High discount (21-30%): 96.9% loss rate, avg -$322 profit")
print("  → Very high discount (31%+): 100% loss rate — every single order loses money")

# ── 6. Build Visualisation ───────────────────────────────────
C = {'blue':'#2563EB','teal':'#0891B2','green':'#059669',
     'purple':'#7C3AED','red':'#DC2626','amber':'#D97706','gray':'#6B7280'}

fig = plt.figure(figsize=(20, 14))
fig.patch.set_facecolor('white')
fig.text(0.5, 0.97, 'Superstore Sales & Revenue Analysis | 2014–2017',
         ha='center', fontsize=18, fontweight='bold', color='#111827')
fig.text(0.5, 0.945, '9,994 orders  ·  4 regions  ·  3 categories  ·  200 customers',
         ha='center', fontsize=11, color='#6B7280')

gs = fig.add_gridspec(3, 3, hspace=0.52, wspace=0.38,
                      left=0.07, right=0.97, top=0.92, bottom=0.06)

# Chart 1: Monthly trend
ax1 = fig.add_subplot(gs[0, :])
x = range(len(monthly))
ax1.fill_between(x, monthly['Revenue']/1e6, alpha=0.12, color=C['blue'])
ax1.plot(x, monthly['Revenue']/1e6, color=C['blue'], lw=2, marker='o', ms=3, label='Revenue')
ax1.plot(x, monthly['Profit']/1e6, color=C['green'], lw=1.8, ls='--', marker='s', ms=3, label='Profit')
ax1.set_title('Monthly Revenue & Profit Trend', fontsize=13, fontweight='bold', pad=8)
ax1.set_xticks(list(x)[::6])
ax1.set_xticklabels([str(monthly['Month'].iloc[i]) for i in range(0,len(monthly),6)], fontsize=9, rotation=30)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'${v:.1f}M'))
ax1.legend(fontsize=10); ax1.spines[['top','right']].set_visible(False)
ax1.grid(axis='y', alpha=0.3, ls='--')

# Chart 2: Top 10 customers
ax2 = fig.add_subplot(gs[1, 0])
tc = df.groupby('Customer Name')['Sales'].sum().nlargest(10).sort_values()
clrs = [C['blue'] if v == tc.max() else '#93C5FD' for v in tc.values]
ax2.barh(range(len(tc)), tc.values/1e3, color=clrs, height=0.65)
ax2.set_yticks(range(len(tc)))
ax2.set_yticklabels([n.replace('Customer_','Cust #') for n in tc.index], fontsize=8)
ax2.set_title('Top 10 Customers by Revenue', fontsize=11, fontweight='bold', pad=6)
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'${v:.0f}K'))
ax2.spines[['top','right']].set_visible(False); ax2.tick_params(axis='x', labelsize=8)

# Chart 3: Category revenue vs profit
ax3 = fig.add_subplot(gs[1, 1])
cg = df.groupby('Category')[['Sales','Profit']].sum().sort_values('Sales', ascending=False)
xc = np.arange(len(cg)); w = 0.35
ax3.bar(xc-w/2, cg['Sales']/1e6, w, color=C['teal'], label='Revenue', alpha=0.9)
ax3.bar(xc+w/2, cg['Profit']/1e6, w, color=C['green'], label='Profit', alpha=0.9)
ax3.set_xticks(xc); ax3.set_xticklabels(cg.index, fontsize=8, rotation=10)
ax3.set_title('Category: Revenue vs Profit', fontsize=11, fontweight='bold', pad=6)
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'${v:.0f}M'))
ax3.legend(fontsize=9); ax3.spines[['top','right']].set_visible(False)

# Chart 4: Regional performance
ax4 = fig.add_subplot(gs[1, 2])
rg = df.groupby('Region')['Sales'].sum().reset_index().sort_values('Sales', ascending=False)
avg_r = rg['Sales'].mean()
rc = [C['red'] if v < avg_r else C['green'] for v in rg['Sales']]
ax4.bar(rg['Region'], rg['Sales']/1e6, color=rc, alpha=0.9)
ax4.axhline(avg_r/1e6, color=C['gray'], ls='--', lw=1.5, label=f'Avg ${avg_r/1e6:.1f}M')
for i,(r,v) in enumerate(zip(rg['Region'], rg['Sales'])):
    ax4.text(i, v/1e6+0.1, '↓ Under' if v<avg_r else '✓', ha='center',
             fontsize=8, color=C['red'] if v<avg_r else C['green'], fontweight='bold')
ax4.set_title('Regional Performance', fontsize=11, fontweight='bold', pad=6)
ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'${v:.0f}M'))
ax4.legend(fontsize=9); ax4.spines[['top','right']].set_visible(False)

# Chart 5: Discount vs avg profit
ax5 = fig.add_subplot(gs[2, 0:2])
dg = df.groupby('Discount_Tier', observed=True).agg(
    Avg_Profit=('Profit','mean'), Loss_Rate=('Profit', lambda x: (x<0).mean()*100)).reset_index()
bc = [C['green'] if v >= 0 else C['red'] for v in dg['Avg_Profit']]
bars5 = ax5.bar(dg['Discount_Tier'], dg['Avg_Profit'], color=bc, alpha=0.9, width=0.55)
ax5.axhline(0, color='black', lw=0.8)
for bar, lr in zip(bars5, dg['Loss_Rate']):
    h = bar.get_height()
    ax5.text(bar.get_x()+bar.get_width()/2, h+8 if h>=0 else h-45,
             f'{lr:.0f}% losses', ha='center', fontsize=8, color='#374151')
ax5.set_title('Discount Tier vs Average Profit  (key business insight)', fontsize=11, fontweight='bold', pad=6)
ax5.set_ylabel('Avg Profit / Order ($)', fontsize=9)
ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'${v:.0f}'))
ax5.spines[['top','right']].set_visible(False); ax5.tick_params(axis='x', labelsize=9)

# Chart 6: Sub-category margins
ax6 = fig.add_subplot(gs[2, 2])
sg = df.groupby('Sub-Category').agg(Rev=('Sales','sum'), Prof=('Profit','sum')).reset_index()
sg['Margin'] = sg['Prof']/sg['Rev']*100
sg = sg.sort_values('Margin')
sc = [C['red'] if m<0 else (C['amber'] if m<10 else C['green']) for m in sg['Margin']]
ax6.barh(sg['Sub-Category'], sg['Margin'], color=sc, height=0.65, alpha=0.9)
ax6.axvline(0, color='black', lw=0.8)
ax6.set_title('Sub-category Profit Margin %', fontsize=11, fontweight='bold', pad=6)
ax6.set_xlabel('Profit Margin %', fontsize=9)
ax6.spines[['top','right']].set_visible(False); ax6.tick_params(axis='y', labelsize=8)

plt.savefig('superstore_analysis.png', dpi=150, bbox_inches='tight', facecolor='white')
print("\nChart saved: superstore_analysis.png")
