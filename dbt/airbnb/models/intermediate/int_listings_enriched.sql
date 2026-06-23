WITH listings AS (
    SELECT * FROM {{ ref('stg_listings') }}
),

reviews AS (
    SELECT
        listing_id,
        COUNT(*) AS total_reviews,
        MIN(review_date) AS first_review,
        MAX(review_date) AS last_review
    FROM {{ ref('stg_reviews') }}
    GROUP BY listing_id
),

calendar_stats AS (
    SELECT
        listing_id,
        AVG(CASE WHEN is_available THEN NULL ELSE price END) AS avg_price,
        SUM(CASE WHEN is_available THEN 1 ELSE 0 END) AS available_days,
        COUNT(*) AS total_days,
        ROUND(SUM(CASE WHEN is_available THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS occupancy_rate_pct
    FROM {{ ref('stg_calendar') }}
    GROUP BY listing_id
)

SELECT
    l.*,
    COALESCE(r.total_reviews, 0) AS total_reviews,
    r.first_review,
    r.last_review,
    cs.avg_price AS avg_calendar_price,
    cs.available_days,
    cs.total_days,
    cs.occupancy_rate_pct,
    CASE
        WHEN l.price < 5000 THEN 'Budget'
        WHEN l.price < 15000 THEN 'Mid-range'
        WHEN l.price < 30000 THEN 'Premium'
        ELSE 'Luxury'
    END AS price_tier,
    CASE
        WHEN l.review_scores_rating >= 95 THEN 'Excellent'
        WHEN l.review_scores_rating >= 85 THEN 'Great'
        WHEN l.review_scores_rating >= 70 THEN 'Good'
        WHEN l.review_scores_rating IS NOT NULL THEN 'Fair'
        ELSE 'Unrated'
    END AS rating_category
FROM listings l
LEFT JOIN reviews r ON l.listing_id = r.listing_id
LEFT JOIN calendar_stats cs ON l.listing_id = cs.listing_id
