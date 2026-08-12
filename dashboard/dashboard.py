"""
dashboard/dashboard.py

RevenueLens interactive dashboard — built with Streamlit + Plotly.
Supports interactive Light/Dark Glassmorphism themes.
Connects to SQLite DB with date, region, and category filters.

Run: streamlit run dashboard/dashboard.py
"""

import sqlite3
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="RevenueLens | Analytics",
    page_icon="lens",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar Filter Setup & Theme Switcher ─────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "revenuelens.db")

@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql):
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql(sql, con)

with st.sidebar:
    st.markdown("<h2 style='font-weight:700; margin-bottom:2px;'>RevenueLens</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.85rem; margin-top:-6px; font-weight:400;'>E-Commerce Analytics</p>", unsafe_allow_html=True)
    
    # Theme Toggle
    theme = st.radio("🎨 App Theme", ["Light Glass", "Dark Glass"], index=0, horizontal=True)
    st.divider()
    st.markdown("<p style='font-size:0.95rem; font-weight:600;'>Filters</p>", unsafe_allow_html=True)

    date_df  = run_query("SELECT MIN(order_date) AS mn, MAX(order_date) AS mx FROM orders")
    min_date = pd.to_datetime(date_df["mn"].iloc[0]).date()
    max_date = pd.to_datetime(date_df["mx"].iloc[0]).date()

    date_range = st.date_input("Date Range", value=(min_date, max_date),
                               min_value=min_date, max_value=max_date)
    start_date = str(date_range[0]) if len(date_range) >= 1 else str(min_date)
    end_date   = str(date_range[1]) if len(date_range) == 2 else str(max_date)

    regions_all      = run_query("SELECT DISTINCT region FROM customers ORDER BY region")["region"].tolist()
    selected_regions = st.multiselect("Region", options=regions_all, default=regions_all)

    cats_all      = run_query("SELECT DISTINCT category FROM products ORDER BY category")["category"].tolist()
    selected_cats = st.multiselect("Category", options=cats_all, default=cats_all)

    st.divider()
    st.caption("Data: Jan 2024 - Dec 2025 DB:\nRevenuelens.db")

if not selected_regions or not selected_cats:
    st.warning("Select at least one region and one category to continue.")
    st.stop()

is_dark = (theme == "Dark Glass")

# ── Dynamic CSS Injection (Light vs Dark Glassmorphism) ──────────────────────
if not is_dark:
    # Light Mode Glassmorphism
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp {
            background-color: #F4F5F9;
            background-image: 
                radial-gradient(circle at 10% 15%, rgba(255, 107, 0, 0.07) 0%, transparent 40%),
                radial-gradient(circle at 90% 65%, rgba(255, 140, 0, 0.05) 0%, transparent 45%);
            background-attachment: fixed; color: #111827;
        }
        [data-testid="stSidebar"] {
            background: rgba(236, 238, 243, 0.8) !important;
            backdrop-filter: blur(24px) saturate(160%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.8) !important;
        }
        [data-testid="stSidebar"] * { color: #1F2937 !important; }
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
            background: rgba(255, 255, 255, 0.75) !important;
            border: 1px solid rgba(209, 213, 219, 0.8) !important;
            border-radius: 12px !important; color: #111827 !important;
        }
        span[data-baseweb="tag"] {
            background: rgba(255, 255, 255, 0.85) !important;
            border: 1px solid rgba(209, 213, 219, 0.8) !important;
        }
        span[data-baseweb="tag"] span { color: #374151 !important; }
        .app-main-title { font-size: 2.2rem; font-weight: 700; color: #111827; margin-bottom: 2px; }
        .app-main-subtitle { font-size: 0.9rem; color: #6B7280; }
        .kpi-card {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(255, 255, 255, 0.85);
            border-radius: 18px; padding: 20px 22px 18px 22px;
            backdrop-filter: blur(20px) saturate(180%);
            box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.95), 0 10px 25px -5px rgba(0, 0, 0, 0.04);
            transition: all 300ms cubic-bezier(0.16, 1, 0.3, 1);
            display: flex; flex-direction: column; justify-content: space-between;
        }
        .kpi-card:hover {
            transform: translateY(-4px) scale(1.008);
            background: rgba(255, 255, 255, 0.92);
            border-color: rgba(217, 82, 0, 0.40);
            box-shadow: inset 0 1px 2px 0 rgba(255, 255, 255, 1.0), 0 20px 40px -10px rgba(217, 82, 0, 0.15);
        }
        .kpi-label { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #4B5563; }
        .kpi-value { font-size: 1.95rem; font-weight: 700; color: #111827; line-height: 1.15; }
        .kpi-delta { font-size: 0.75rem; color: #D95200; margin-top: 6px; font-weight: 500; }
        .section-header { font-size: 1.05rem; font-weight: 600; color: #111827; border-left: 3.5px solid #D95200; padding-left: 10px; margin: 24px 0 14px 0; }
        div[data-testid="stPlotlyChart"] {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(255, 255, 255, 0.85);
            border-radius: 18px; padding: 16px 18px 8px 18px;
            backdrop-filter: blur(20px) saturate(180%);
            box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.95), 0 10px 25px -5px rgba(0, 0, 0, 0.04);
            transition: all 300ms cubic-bezier(0.16, 1, 0.3, 1);
        }
        div[data-testid="stPlotlyChart"]:hover {
            transform: translateY(-3px) scale(1.004);
            background: rgba(255, 255, 255, 0.90);
            border-color: rgba(217, 82, 0, 0.35);
        }
    </style>
    """, unsafe_allow_html=True)
else:
    # Dark Mode Glassmorphism
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp {
            background-color: #0A0A0C;
            background-image: 
                radial-gradient(circle at 15% 20%, rgba(255, 107, 0, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 85% 70%, rgba(255, 136, 0, 0.06) 0%, transparent 55%);
            background-attachment: fixed; color: #F5F5F7;
        }
        [data-testid="stSidebar"] {
            background: rgba(20, 20, 26, 0.8) !important;
            backdrop-filter: blur(24px) saturate(140%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }
        [data-testid="stSidebar"] * { color: #E0E0E6 !important; }
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 12px !important; color: #FFFFFF !important;
        }
        span[data-baseweb="tag"] {
            background: rgba(255, 107, 0, 0.15) !important;
            border: 1px solid rgba(255, 107, 0, 0.4) !important;
        }
        span[data-baseweb="tag"] span { color: #FF8800 !important; }
        .app-main-title { font-size: 2.2rem; font-weight: 700; color: #FFFFFF; margin-bottom: 2px; }
        .app-main-subtitle { font-size: 0.9rem; color: rgba(255,255,255,0.6); }
        .kpi-card {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px; padding: 20px 22px 18px 22px;
            backdrop-filter: blur(24px);
            box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.06), 0 10px 25px rgba(0, 0, 0, 0.35);
            transition: all 300ms cubic-bezier(0.16, 1, 0.3, 1);
            display: flex; flex-direction: column; justify-content: space-between;
        }
        .kpi-card:hover {
            transform: translateY(-4px) scale(1.008);
            background: rgba(255, 107, 0, 0.05);
            border-color: rgba(255, 107, 0, 0.40);
            box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.10), 0 20px 40px rgba(255, 107, 0, 0.12);
        }
        .kpi-label { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: rgba(255, 255, 255, 0.6); }
        .kpi-value { font-size: 1.95rem; font-weight: 700; color: #FFFFFF; line-height: 1.15; }
        .kpi-delta { font-size: 0.75rem; color: #FF9933; margin-top: 6px; font-weight: 500; }
        .section-header { font-size: 1.05rem; font-weight: 600; color: #FFFFFF; border-left: 3.5px solid #FF6B00; padding-left: 10px; margin: 24px 0 14px 0; }
        div[data-testid="stPlotlyChart"] {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px; padding: 16px 18px 8px 18px;
            backdrop-filter: blur(24px);
            box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.06), 0 10px 25px rgba(0, 0, 0, 0.35);
            transition: all 300ms cubic-bezier(0.16, 1, 0.3, 1);
        }
        div[data-testid="stPlotlyChart"]:hover {
            transform: translateY(-3px) scale(1.004);
            border-color: rgba(255, 107, 0, 0.35);
        }
    </style>
    """, unsafe_allow_html=True)


PLOTLY_TEMPLATE = "plotly_dark" if is_dark else "plotly_white"
GRID_COLOR      = "rgba(255, 255, 255, 0.05)" if is_dark else "#E5E7EB"
TEXT_COLOR      = "#E0E0E6" if is_dark else "#374151"
MUTED_TEXT      = "rgba(255,255,255,0.5)" if is_dark else "#6B7280"

def style_fig(fig, height=360):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=16, r=16, t=30, b=16),
        font=dict(family="Inter", color=TEXT_COLOR, size=11),
        xaxis=dict(
            gridcolor=GRID_COLOR,
            griddash="dot",
            zeroline=False,
            showgrid=False,
            tickfont=dict(color=MUTED_TEXT)
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            griddash="dot",
            zeroline=False,
            tickfont=dict(color=MUTED_TEXT)
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=TEXT_COLOR)),
    )
    return fig


region_in = ",".join(f"'{r}'" for r in selected_regions)
cat_in    = ",".join(f"'{c}'" for c in selected_cats)

# Reusable filtered CTE — joins all 4 tables with filters applied
FILTER_CTE = f"""
WITH base AS (
    SELECT o.order_id, o.customer_id, o.order_date, o.status,
           oi.order_item_id, oi.product_id, oi.quantity, oi.unit_price, oi.discount,
           p.category, p.sub_category, p.price, p.cost,
           c.region, c.segment,
           ROUND(oi.quantity * oi.unit_price * (1 - oi.discount), 2) AS line_revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id   = o.order_id
    JOIN products   p  ON p.product_id   = oi.product_id
    JOIN customers  c  ON c.customer_id  = o.customer_id
    WHERE o.status IN ('Delivered','Shipped')
      AND o.order_date BETWEEN '{start_date}' AND '{end_date}'
      AND c.region   IN ({region_in})
      AND p.category IN ({cat_in})
)
"""

# Header
st.markdown("""
<div class="app-title-container">
    <div class="app-main-title">RevenueLens</div>
    <div class="app-main-subtitle">E-Commerce Sales Analytics &nbsp;·&nbsp; Executive Overview</div>
</div>
""", unsafe_allow_html=True)

# KPI cards
kpi = run_query(f"""
{FILTER_CTE}
SELECT
    ROUND(SUM(line_revenue), 2) AS total_revenue,
    COUNT(DISTINCT order_id)    AS total_orders,
    ROUND(SUM(line_revenue) / COUNT(DISTINCT order_id), 2) AS avg_order_value,
    COUNT(DISTINCT customer_id) AS active_customers
FROM base
""")

total_rev   = kpi["total_revenue"].iloc[0] or 0
total_ord   = int(kpi["total_orders"].iloc[0] or 0)
avg_ov      = kpi["avg_order_value"].iloc[0] or 0
active_cust = int(kpi["active_customers"].iloc[0] or 0)

k1, k2, k3, k4 = st.columns(4)

accent_color = "#FF6B00" if is_dark else "#D95200"
icons = [
    f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{accent_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',
    f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{accent_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 0 1-8 0"></path></svg>',
    f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{accent_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>',
    f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{accent_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
]

cards_data = [
    (k1, "TOTAL REVENUE",     f"${total_rev:,.0f}",  "3-year cumulative", icons[0]),
    (k2, "TOTAL ORDERS",      f"{total_ord:,}",       "delivered + shipped", icons[1]),
    (k3, "AVG ORDER VALUE",   f"${avg_ov:,.2f}",      "per order", icons[2]),
    (k4, "ACTIVE CUSTOMERS",  f"{active_cust:,}",     "with 1+ order", icons[3]),
]

for col, label, value, delta, icon in cards_data:
    col.markdown(f"""
    <div class='kpi-card'>
        <div>
            <div class='kpi-header-row'>
                <div class='kpi-label'>{label}</div>
                <div class='kpi-icon'>{icon}</div>
            </div>
            <div class='kpi-value'>{value}</div>
        </div>
        <div class='kpi-delta'>{delta}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Revenue trend
st.markdown("<div class='section-header'>Revenue Trend Over Time</div>", unsafe_allow_html=True)

trend = run_query(f"""
{FILTER_CTE}
SELECT strftime('%Y-%m', order_date) AS month,
       ROUND(SUM(line_revenue), 2)   AS revenue,
       COUNT(DISTINCT order_id)      AS orders
FROM base GROUP BY 1 ORDER BY 1
""")

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=trend["month"], y=trend["revenue"],
    mode="lines+markers",
    name="Revenue",
    line=dict(color=accent_color, width=2.8, shape="spline"),
    marker=dict(size=6, color=accent_color),
    fill="tozeroy",
    fillcolor="rgba(217, 82, 0, 0.12)" if not is_dark else "rgba(255, 107, 0, 0.12)",
    hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
))
fig_trend.update_layout(title="Monthly Revenue (USD)", xaxis_title="Month",
                        yaxis_tickprefix="$", yaxis_tickformat=",")
style_fig(fig_trend, height=330)
st.plotly_chart(fig_trend, use_container_width=True)

# Top products + region side by side
c1, c2 = st.columns([3, 2])

with c1:
    st.markdown("<div class='section-header'>Top 10 Products by Revenue</div>", unsafe_allow_html=True)
    prod_df = run_query(f"""
    {FILTER_CTE}
    SELECT p2.name AS product_name, p2.category,
           ROUND(SUM(b.line_revenue), 2) AS revenue
    FROM base b
    JOIN products p2 ON p2.product_id = b.product_id
    GROUP BY b.product_id, p2.name, p2.category
    ORDER BY revenue DESC LIMIT 10
    """)

    orange_gradient = ["#D95200", "#E66000", "#F57C00", "#FB8C00", "#FFB74D"] if not is_dark else ["#FF5500", "#FF6B00", "#FF8800", "#FF9900", "#FFAA00"]
    fig_prod = px.bar(prod_df.sort_values("revenue"),
                      x="revenue", y="product_name", color="category",
                      orientation="h",
                      color_discrete_sequence=orange_gradient,
                      labels={"revenue": "Revenue (USD)", "product_name": ""},
                      title="Top 10 Products")
    fig_prod.update_traces(hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>")
    fig_prod.update_layout(xaxis_tickprefix="$", xaxis_tickformat=",")
    style_fig(fig_prod, height=380)
    st.plotly_chart(fig_prod, use_container_width=True)

with c2:
    st.markdown("<div class='section-header'>Revenue by Region</div>", unsafe_allow_html=True)
    region_df = run_query(f"""
    {FILTER_CTE}
    SELECT region, ROUND(SUM(line_revenue), 2) AS revenue,
           COUNT(DISTINCT order_id) AS orders
    FROM base GROUP BY region ORDER BY revenue DESC
    """)

    fig_reg = px.bar(region_df, x="region", y="revenue", color="region",
                     color_discrete_sequence=["#D95200", "#F57C00", "#FFB74D", "#9CA3AF"] if not is_dark else ["#FF6B00", "#FF8800", "#FFAA44", "#E0E0E0"],
                     labels={"revenue": "Revenue (USD)", "region": ""},
                     title="Revenue by Region", text_auto=".2s")
    fig_reg.update_traces(
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<br>Orders: %{customdata[0]:,}<extra></extra>",
        customdata=region_df[["orders"]].values,
    )
    fig_reg.update_layout(showlegend=False, yaxis_tickprefix="$", yaxis_tickformat=",")
    style_fig(fig_reg, height=380)
    st.plotly_chart(fig_reg, use_container_width=True)

# RFM + Category
c3, c4 = st.columns([2, 3])

with c3:
    st.markdown("<div class='section-header'>RFM Segment Distribution</div>", unsafe_allow_html=True)

    rfm_df = run_query(f"""
    WITH rfm_raw AS (
        SELECT c.customer_id,
            CAST(julianday('2026-01-01') - julianday(MAX(o.order_date)) AS INTEGER) AS recency_days,
            COUNT(DISTINCT o.order_id) AS frequency,
            ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS monetary
        FROM customers c
        JOIN orders      o  ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id   = o.order_id
        JOIN products    p  ON p.product_id  = oi.product_id
        WHERE o.status IN ('Delivered','Shipped')
          AND o.order_date BETWEEN '{start_date}' AND '{end_date}'
          AND c.region   IN ({region_in})
          AND p.category IN ({cat_in})
        GROUP BY c.customer_id
    ),
    rfm_scored AS (
        SELECT *,
            NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
            NTILE(4) OVER (ORDER BY frequency   ASC)  AS f_score,
            NTILE(4) OVER (ORDER BY monetary    ASC)  AS m_score
        FROM rfm_raw
    )
    SELECT
        CASE
            WHEN r_score = 4 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3                  THEN 'Loyal'
            WHEN r_score = 4                                     THEN 'Recent'
            WHEN r_score >= 2 AND m_score >= 3                   THEN 'Potential Loyalist'
            WHEN r_score <= 2 AND f_score >= 3                   THEN 'At Risk'
            WHEN r_score = 1  AND f_score >= 2                   THEN 'Lost'
            ELSE                                                       'Needs Attention'
        END AS rfm_segment,
        COUNT(*) AS customers
    FROM rfm_scored
    GROUP BY rfm_segment
    ORDER BY customers DESC
    """)

    SEG_COLORS = {
        "Champions": accent_color, 
        "Loyal": "#E66000" if not is_dark else "#FF8800",
        "Potential Loyalist": "#F57C00" if not is_dark else "#FFA022", 
        "Recent": "#FFB74D" if not is_dark else "#FFB855",
        "Needs Attention": "#9CA3AF" if not is_dark else "#888899", 
        "At Risk": "#EF4444" if not is_dark else "#D9534F", 
        "Lost": "#6B7280" if not is_dark else "#555566"
    }

    fig_rfm = px.pie(rfm_df, names="rfm_segment", values="customers",
                     color="rfm_segment", color_discrete_map=SEG_COLORS,
                     hole=0.52, title="Customer RFM Segments")
    fig_rfm.update_traces(textposition="outside", textinfo="label+percent",
                          hovertemplate="<b>%{label}</b><br>%{value:,} customers<extra></extra>")
    fig_rfm.update_layout(showlegend=False)
    style_fig(fig_rfm, height=380)
    st.plotly_chart(fig_rfm, use_container_width=True)

with c4:
    st.markdown("<div class='section-header'>Revenue by Category</div>", unsafe_allow_html=True)
    cat_df = run_query(f"""
    {FILTER_CTE}
    SELECT category,
           ROUND(SUM(line_revenue), 2) AS revenue,
           SUM(quantity)               AS units_sold,
           COUNT(DISTINCT order_id)    AS orders
    FROM base GROUP BY category ORDER BY revenue DESC
    """)

    fig_cat = px.bar(cat_df, x="category", y="revenue", color="category",
                     color_discrete_sequence=["#D95200", "#E66000", "#F57C00", "#FFB74D", "#9CA3AF"] if not is_dark else ["#FF6B00", "#FF851B", "#FFA500", "#FFC04D", "#FFFFFF"],
                     labels={"revenue": "Revenue (USD)", "category": ""},
                     title="Revenue by Category", text_auto=".2s")
    fig_cat.update_traces(
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<br>Units: %{customdata[0]:,}<extra></extra>",
        customdata=cat_df[["units_sold"]].values,
    )
    fig_cat.update_layout(showlegend=False, yaxis_tickprefix="$", yaxis_tickformat=",")
    style_fig(fig_cat, height=380)
    st.plotly_chart(fig_cat, use_container_width=True)

st.divider()
st.markdown(
    f"<p style='text-align:center; color:{MUTED_TEXT}; font-size:0.8rem;'>"
    "RevenueLens &nbsp;·&nbsp; Streamlit + Plotly &nbsp;·&nbsp; Dual Light &amp; Dark Glassmorphism"
    "</p>",
    unsafe_allow_html=True
)
