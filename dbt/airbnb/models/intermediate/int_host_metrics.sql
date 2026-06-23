WITH listings AS (
    SELECT * FROM {{ ref('stg_listings') }}
),

host_summary AS (
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
        COUNT(*) AS num_listings,
        ROUND(AVG(price), 2) AS avg_listing_price,
        ROUND(AVG(review_scores_rating), 1) AS avg_review_score,
        SUM(number_of_reviews) AS total_reviews_received,
        ROUND(AVG(reviews_per_month), 2) AS avg_reviews_per_month,
        ROUND(AVG(availability_365), 0) AS avg_availability_days
    FROM listings
    GROUP BY host_id, host_name, host_since, host_location, host_response_time,
             host_response_rate, host_acceptance_rate, host_is_superhost,
             host_neighbourhood, host_total_listings_count
)

SELECT * FROM host_summary
