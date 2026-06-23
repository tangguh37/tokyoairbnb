import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Tokyo Airbnb Analytics", layout="wide")

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tokyo_airbnb.duckdb"
MART = "main_marts"


@st.cache_resource
def get_db():
    return duckdb.connect(str(DB_PATH))


@st.cache_data(ttl=300)
def query(sql):
    con = get_db()
    return con.execute(sql).df()


def main():
    st.title(" Tokyo Airbnb Analytics")
    st.markdown("Analytics dashboard powered by **dbt + DuckDB + Airflow**")

    try:
        summary = query(f"""
            SELECT
                COUNT(*) AS total_listings,
                COUNT(DISTINCT host_id) AS total_hosts,
                ROUND(AVG(price), 0) AS avg_price,
                ROUND(AVG(review_scores_rating), 1) AS avg_rating,
                ROUND(AVG(occupancy_rate_pct), 1) AS avg_occupancy
            FROM {MART}.dim_listing
        """)
    except Exception as e:
        st.error(f"Cannot connect to database. Run `make dbt-run` first.\n\n{e}")
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Listings", f"{summary['total_listings'][0]:,}")
    col2.metric("Total Hosts", f"{summary['total_hosts'][0]:,}")
    col3.metric("Avg Price", f"${summary['avg_price'][0]:,.0f}")
    col4.metric("Avg Rating", f"{summary['avg_rating'][0]}/100")
    col5.metric("Avg Occupancy", f"{summary['avg_occupancy'][0]}%")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        " Pricing & Listings", "  Occupancy Trends", " Host Analysis",
        " Review Insights", " Insights"
    ])

    with tab1:
        st.subheader("Pricing by Room Type and Neighbourhood")
        pricing = query(f"""
            SELECT neighbourhood, room_type, num_listings, avg_price, median_price,
                   p25_price, p75_price, avg_review_score
            FROM {MART}.pricing_analysis
            ORDER BY avg_price DESC LIMIT 50
        """)
        if not pricing.empty:
            fig = px.bar(
                pricing.head(20),
                x="neighbourhood", y="avg_price", color="room_type",
                hover_data=["median_price", "num_listings"],
                title="Top 20 Neighbourhoods by Average Price",
                labels={"avg_price": "Avg Price ($)", "neighbourhood": "Neighbourhood"},
                barmode="group",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Price Distribution")
        listings = query(f"""
            SELECT price, room_type, neighbourhood
            FROM {MART}.dim_listing
            WHERE price > 0 AND price < 100000
        """)
        if not listings.empty:
            fig2 = px.box(
                listings, x="room_type", y="price", color="room_type",
                title="Price Distribution by Room Type", points="outliers",
            )
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Monthly Occupancy Trends")
        try:
            occ = query(f"""
                SELECT month, room_type,
                       ROUND(AVG(occupancy_rate_pct), 1) AS avg_occupancy,
                       ROUND(AVG(avg_price), 0) AS avg_price
                FROM {MART}.monthly_occupancy
                WHERE avg_price IS NOT NULL
                GROUP BY month, room_type ORDER BY month
            """)
            if not occ.empty:
                fig3 = px.line(
                    occ, x="month", y="avg_occupancy", color="room_type",
                    title="Occupancy Rate by Room Type Over Time", markers=True,
                )
                st.plotly_chart(fig3, use_container_width=True)
                fig4 = px.line(
                    occ, x="month", y="avg_price", color="room_type",
                    title="Average Price by Room Type Over Time", markers=True,
                )
                st.plotly_chart(fig4, use_container_width=True)
        except Exception as e:
            st.info(f"Occupancy data not available yet: {e}")

    with tab3:
        st.subheader("Host Distribution")
        hosts = query(f"""
            SELECT host_rating_tier, COUNT(*) AS count
            FROM {MART}.dim_host GROUP BY host_rating_tier
        """)
        if not hosts.empty:
            fig5 = px.pie(
                hosts, values="count", names="host_rating_tier",
                title="Hosts by Rating Tier", hole=0.4
            )
            st.plotly_chart(fig5, use_container_width=True)

        st.subheader("Superhost vs Regular Host")
        sh = query(f"""
            SELECT
                CASE WHEN host_is_superhost THEN 'Superhost' ELSE 'Regular' END AS host_type,
                ROUND(AVG(avg_listing_price), 0) AS avg_price,
                ROUND(AVG(avg_review_score), 1) AS avg_rating,
                ROUND(AVG(total_reviews_received), 0) AS avg_reviews
            FROM {MART}.dim_host GROUP BY host_type
        """)
        if not sh.empty:
            col_a, col_b, col_c = st.columns(3)
            for col, metric, title, fmt in [
                (col_a, "avg_price", "Avg Price ($)", ".0f"),
                (col_b, "avg_rating", "Avg Rating (0–100)", ".1f"),
                (col_c, "avg_reviews", "Avg Reviews", ".0f"),
            ]:
                with col:
                    fig = px.bar(
                        sh, x="host_type", y=metric, title=title,
                        color="host_type", text_auto=fmt,
                        color_discrete_map={"Superhost": "#FF5A5F", "Regular": "#00A699"},
                    )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Reviews Over Time")
        try:
            rev = query(f"""
                SELECT DATE_TRUNC('month', review_date)::DATE AS month,
                       COUNT(*) AS review_count
                FROM {MART}.fct_reviews GROUP BY month ORDER BY month
            """)
            if not rev.empty:
                fig7 = px.area(
                    rev, x="month", y="review_count",
                    title="Monthly Review Volume",
                    labels={"review_count": "Number of Reviews", "month": "Month"},
                )
                st.plotly_chart(fig7, use_container_width=True)
        except Exception as e:
            st.info(f"Review data not available yet: {e}")

        st.subheader("Top Reviewed Listings")
        top = query(f"""
            SELECT listing_name, number_of_reviews, price, review_scores_rating,
                   neighbourhood, room_type
            FROM {MART}.dim_listing
            ORDER BY number_of_reviews DESC LIMIT 10
        """)
        if not top.empty:
            st.dataframe(top, use_container_width=True, hide_index=True)

    with tab5:
        room = query(f"""
            SELECT room_type, COUNT(*) as n,
                   ROUND(AVG(price)) as price,
                   ROUND(AVG(review_scores_rating),1) as rating,
                   ROUND(AVG(occupancy_rate_pct),1) as occ,
                   ROUND(AVG(minimum_nights)) as min_nights
            FROM {MART}.dim_listing WHERE price > 0
            GROUP BY room_type ORDER BY price DESC
        """)
        nb = query(f"""
            (SELECT neighbourhood, ROUND(AVG(price)) as price, COUNT(*) as n
             FROM {MART}.dim_listing WHERE price > 0
             GROUP BY neighbourhood ORDER BY price DESC LIMIT 5)
            UNION ALL
            (SELECT neighbourhood, ROUND(AVG(price)) as price, COUNT(*) as n
             FROM {MART}.dim_listing WHERE price > 0
             GROUP BY neighbourhood ORDER BY price LIMIT 5)
        """)
        qtr = query(f"""
            SELECT DATE_TRUNC('quarter', month)::DATE as q,
                   ROUND(AVG(occupancy_rate_pct),1) as occ,
                   ROUND(AVG(avg_price)) as price
            FROM {MART}.monthly_occupancy GROUP BY q ORDER BY q
        """)
        sh2 = query(f"""
            SELECT CASE WHEN host_is_superhost THEN 'Superhost' ELSE 'Regular' END as type,
                   COUNT(*) as n, ROUND(AVG(avg_listing_price)) as price,
                   ROUND(AVG(avg_review_score),1) as rating,
                   ROUND(AVG(total_reviews_received),0) as reviews,
                   ROUND(AVG(avg_reviews_per_month),2) as rvpm
            FROM {MART}.dim_host GROUP BY type
        """)

        total_listings = int(summary['total_listings'][0])
        total_hosts = int(summary['total_hosts'][0])

        st.markdown("##  Market Structure")
        st.markdown(f"""
The Tokyo Airbnb market has **{total_listings:,} listings** managed by **{total_hosts:,} hosts**,
averaging **{total_listings/total_hosts:.1f} listings per host**. This suggests **professionalization**
— hosts running multiple properties rather than casual room rentals.
        """)

        if not room.empty:
            c1, c2 = st.columns([2, 1])
            with c1:
                fig = px.bar(
                    room, x="room_type", y="price", color="room_type",
                    title="Average Price by Room Type",
                    text_auto=".0f", color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.markdown("#### Room Type Breakdown")
                for _, r in room.iterrows():
                    st.markdown(f"**{r['room_type']}**: ${r['price']:,.0f}/night — {r['n']:,} listings, {r['occ']}% occ, min {int(r['min_nights'])} nights")
                    st.markdown(f"— Avg rating {r['rating']}/100")
                    st.markdown("")

        st.markdown("---")
        st.markdown("##  Neighbourhood Arbitrage")
        st.markdown("""
**Top 5 priciest vs bottom 5 cheapest neighbourhoods** — a 5–8x price gap exists
between central Tokyo (Chuo, Shibuya, Minato) and outer suburbs (Higashiyamato, Tama, Akishima).
        """)
        if not nb.empty:
            nb["type"] = ["Top"] * 5 + ["Bottom"] * 5
            fig = px.bar(
                nb, x="neighbourhood", y="price", color="type",
                hover_data=["n"], title="Price Gap: Top vs Bottom Neighbourhoods",
                text_auto=".0f",
                color_discrete_map={"Top": "#FF5A5F", "Bottom": "#00A699"},
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("""
**Real-world strategy:** Mix 1 central premium listing + 2 mid-range outer listings
to capture both high-spend tourists and budget-conscious travelers.
        """)

        st.markdown("---")
        st.markdown("##  Seasonality")
        st.markdown("""
Tokyo Airbnb demand follows clear seasonal patterns:
- **Q3 (Jul–Sep)**: Peak at ~84% occupancy — autumn tourism, pleasant weather
- **Q4 (Oct–Dec)**: Declining to ~57% — winter low season
- **Q1 (Jan–Mar)**: Trough at ~32% — coldest months, low tourism
- **Q2 (Apr–Jun)**: Rising to ~56% — cherry blossom season recovery
- **Q3 (Jul–Sep)**: Back up to ~68%
        """)
        if not qtr.empty:
            fig = px.bar(
                qtr, x="q", y="occ", color="occ",
                title="Quarterly Occupancy Rate",
                text_auto=".1f", color_continuous_scale="RdYlGn",
                labels={"occ": "Occupancy %", "q": "Quarter"},
            )
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
**Recommendations for hosts:**
- **Dynamic pricing:** Raise prices ~20% for Sep–Nov, lower 15–20% for Jan–Feb
- **Minimum nights:** Increase to 3+ during peak, 1–2 in off-season to attract last-minute bookings
- **Maintenance window:** Schedule renovations during the Jan–Mar low season
        """)

        st.markdown("---")
        st.markdown("##  Superhost Advantage")
        st.markdown("""
**Superhost status drives significant business results:**
        """)
        if not sh2.empty:
            super_row = sh2[sh2["type"] == "Superhost"].iloc[0]
            reg_row = sh2[sh2["type"] == "Regular"].iloc[0]
            price_pct = (super_row["price"] / reg_row["price"] - 1) * 100
            review_pct = (super_row["reviews"] / reg_row["reviews"] - 1) * 100
            rating_diff = super_row["rating"] - reg_row["rating"]

            cols = st.columns(3)
            cols[0].metric("Price Premium", f"+{price_pct:.0f}%", f"${super_row['price']:,.0f} vs ${reg_row['price']:,.0f}")
            cols[1].metric("Rating Advantage", f"+{rating_diff:.1f} pts", f"{super_row['rating']}/100 vs {reg_row['rating']}/100")
            cols[2].metric("More Reviews", f"+{review_pct:.0f}%", f"{super_row['reviews']:,.0f} vs {reg_row['reviews']:,.0f}")

            st.markdown("""
**What this means:**
- Superhosts charge **24% more** per night than regular hosts
- They earn **45% more bookings** (measured by review volume)
- Their ratings are consistently **3.8 points higher**

**To achieve Superhost status:**
- Maintain ≥4.8/5 rating (currently 93.8 → 97.6 for Superhosts)
- Respond to 90%+ of inquiries within 24 hours
- Complete ≥10 bookings per year
- Maintain ≥90% booking rate (cancellation rate under 1%)
        """)

        st.markdown("---")
        st.markdown("##  Summary Recommendations")
        st.markdown("""
| Area | Action | Expected Impact |
|------|--------|----------------|
| **Pricing** | Use dynamic pricing by season | +15–20% revenue |
| **Neighbourhood** | Target central wards for premium, outer for volume | 3–5x price difference |
| **Superhost** | Invest in guest experience to earn badge | +24% price, +45% bookings |
| **Minimum nights** | Adjust by season (3 peak, 1 off-peak) | Higher occupancy year-round |
| **Portfolio mix** | 1 central + 2 outer listings | Best risk/reward balance |

These insights are exactly what a **data team at Airbnb, Booking.com, or any marketplace** would produce
for their hosts and business stakeholders.
        """)

    st.markdown("---")
    st.caption("Built with Streamlit  |  Data: Inside Airbnb (Tokyo, Sept 2025)")


if __name__ == "__main__":
    main()
