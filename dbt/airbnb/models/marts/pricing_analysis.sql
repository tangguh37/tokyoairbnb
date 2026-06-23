WITH listings AS (
    SELECT * FROM {{ ref('dim_listing') }}
)

SELECT
    neighbourhood,
    room_type,
    COUNT(*) AS num_listings,
    ROUND(AVG(price), 2) AS avg_price,
    ROUND(MIN(price), 2) AS min_price,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price), 2) AS p25_price,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price), 2) AS median_price,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price), 2) AS p75_price,
    ROUND(MAX(price), 2) AS max_price,
    ROUND(AVG(review_scores_rating), 1) AS avg_review_score,
    ROUND(AVG(occupancy_rate_pct), 1) AS avg_occupancy_pct,
    ROUND(AVG(reviews_per_month), 2) AS avg_reviews_per_month,
    ROUND(AVG(minimum_nights), 0) AS avg_min_nights
FROM listings
WHERE price > 0
GROUP BY neighbourhood, room_type
HAVING COUNT(*) >= 5
ORDER BY neighbourhood, room_type
