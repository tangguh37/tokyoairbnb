WITH listings AS (
    SELECT DISTINCT neighbourhood
    FROM {{ ref('stg_listings') }}
    WHERE neighbourhood IS NOT NULL
),

neighbourhood_stats AS (
    SELECT
        neighbourhood,
        COUNT(*) AS num_listings,
        ROUND(AVG(price), 2) AS avg_price,
        ROUND(AVG(review_scores_rating), 1) AS avg_review_score,
        ROUND(AVG(availability_365), 0) AS avg_availability_days
    FROM {{ ref('stg_listings') }}
    WHERE neighbourhood IS NOT NULL
    GROUP BY neighbourhood
)

SELECT
    n.neighbourhood,
    COALESCE(s.num_listings, 0) AS num_listings,
    s.avg_price,
    s.avg_review_score,
    s.avg_availability_days
FROM listings n
LEFT JOIN neighbourhood_stats s ON n.neighbourhood = s.neighbourhood
