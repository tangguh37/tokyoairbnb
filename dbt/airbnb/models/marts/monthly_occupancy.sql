WITH calendar AS (
    SELECT * FROM {{ ref('fct_calendar') }}
),

listings AS (
    SELECT listing_id, neighbourhood, room_type
    FROM {{ ref('dim_listing') }}
),

monthly AS (
    SELECT
        DATE_TRUNC('month', calendar_date)::DATE AS month,
        c.listing_id,
        l.neighbourhood,
        l.room_type,
        COUNT(*) AS days_in_month,
        SUM(CASE WHEN c.is_available THEN 0 ELSE 1 END) AS booked_days,
        ROUND(AVG(CASE WHEN NOT c.is_available THEN c.price ELSE NULL END), 2) AS avg_price,
        ROUND(SUM(CASE WHEN NOT c.is_available THEN c.price ELSE 0 END), 2) AS estimated_revenue
    FROM calendar c
    JOIN listings l ON c.listing_id = l.listing_id
    GROUP BY month, c.listing_id, l.neighbourhood, l.room_type
)

SELECT
    month,
    listing_id,
    neighbourhood,
    room_type,
    days_in_month,
    booked_days,
    (days_in_month - booked_days) AS available_days,
    ROUND(booked_days * 100.0 / NULLIF(days_in_month, 0), 1) AS occupancy_rate_pct,
    avg_price,
    estimated_revenue,
    ROUND(estimated_revenue / NULLIF(booked_days, 0), 2) AS avg_daily_rate
FROM monthly
