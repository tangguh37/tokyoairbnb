import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Tokyo Airbnb Analytics", layout="wide")

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tokyo_airbnb.duckdb"

# dbt creates schemas as {custom_schema}_{target_schema}
# e.g., marts + main = main_marts
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

    tab1, tab2, tab3, tab4 = st.tabs([
        " Pricing & Listings", "  Occupancy Trends", " Host Analysis", " Review Insights"
    ])

    with tab1:
        st.subheader("Pricing by Room Type and Neighbourhood")

        pricing = query(f"""
            SELECT neighbourhood, room_type, num_listings, avg_price, median_price,
                   p25_price, p75_price, avg_review_score
            FROM {MART}.pricing_analysis
            ORDER BY avg_price DESC
            LIMIT 50
        """)

        if not pricing.empty:
            fig = px.bar(
                pricing.head(20),
                x="neighbourhood",
                y="avg_price",
                color="room_type",
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
                listings,
                x="room_type",
                y="price",
                color="room_type",
                title="Price Distribution by Room Type",
                points="outliers",
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
                GROUP BY month, room_type
                ORDER BY month
            """)
            if not occ.empty:
                fig3 = px.line(
                    occ,
                    x="month",
                    y="avg_occupancy",
                    color="room_type",
                    title="Occupancy Rate by Room Type Over Time",
                    markers=True,
                )
                st.plotly_chart(fig3, use_container_width=True)

                fig4 = px.line(
                    occ,
                    x="month",
                    y="avg_price",
                    color="room_type",
                    title="Average Price by Room Type Over Time",
                    markers=True,
                )
                st.plotly_chart(fig4, use_container_width=True)
        except Exception as e:
            st.info(f"Run `make dbt-run` to populate occupancy data: {e}")

    with tab3:
        st.subheader("Host Distribution")

        hosts = query(f"""
            SELECT host_rating_tier, COUNT(*) AS count
            FROM {MART}.dim_host
            GROUP BY host_rating_tier
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
            FROM {MART}.dim_host
            GROUP BY host_type
        """)
        if not sh.empty:
            fig6 = px.bar(
                sh.melt(id_vars="host_type"),
                x="host_type", y="value", color="variable",
                title="Superhost vs Regular Host Performance",
                barmode="group",
            )
            st.plotly_chart(fig6, use_container_width=True)

    with tab4:
        st.subheader("Reviews Over Time")
        try:
            rev = query(f"""
                SELECT DATE_TRUNC('month', review_date)::DATE AS month,
                       COUNT(*) AS review_count
                FROM {MART}.fct_reviews
                GROUP BY month
                ORDER BY month
            """)
            if not rev.empty:
                fig7 = px.area(
                    rev, x="month", y="review_count",
                    title="Monthly Review Volume",
                    labels={"review_count": "Number of Reviews", "month": "Month"},
                )
                st.plotly_chart(fig7, use_container_width=True)
        except Exception as e:
            st.info(f"Run `make dbt-run` to populate review data: {e}")

        st.subheader("Top Reviewed Listings")
        top = query(f"""
            SELECT listing_name, number_of_reviews, price, review_scores_rating,
                   neighbourhood, room_type
            FROM {MART}.dim_listing
            ORDER BY number_of_reviews DESC
            LIMIT 10
        """)
        if not top.empty:
            st.dataframe(top, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption("Built with Streamlit  |  Data: Inside Airbnb (Tokyo, Sept 2025)")


if __name__ == "__main__":
    main()
