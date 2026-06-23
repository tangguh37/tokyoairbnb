WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_reviews') }}
),

cleaned AS (
    SELECT
        id AS review_id,
        listing_id,
        date::DATE AS review_date,
        reviewer_id::BIGINT AS reviewer_id,
        reviewer_name,
        comments
    FROM source
)

SELECT * FROM cleaned
