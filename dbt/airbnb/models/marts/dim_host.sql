WITH host_metrics AS (
    SELECT * FROM {{ ref('int_host_metrics') }}
)

SELECT
    host_id,
    host_name,
    host_since,
    host_location,
    host_response_time,
    host_response_rate,
    host_acceptance_rate,
    host_is_superhost,
    host_neighbourhood,
    host_total_listings_count,
    num_listings,
    avg_listing_price,
    avg_review_score,
    total_reviews_received,
    avg_reviews_per_month,
    avg_availability_days,
    CASE
        WHEN host_is_superhost THEN 'Superhost'
        WHEN num_listings >= 5 THEN 'Power Host'
        WHEN num_listings >= 2 THEN 'Multi-listing Host'
        ELSE 'Single-listing Host'
    END AS host_tier,
    CASE
        WHEN avg_review_score >= 95 THEN 'Elite'
        WHEN avg_review_score >= 85 THEN 'Highly Rated'
        WHEN avg_review_score >= 70 THEN 'Average'
        ELSE 'Needs Improvement'
    END AS host_rating_tier
FROM host_metrics
