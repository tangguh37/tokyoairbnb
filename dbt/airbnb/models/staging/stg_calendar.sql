WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_calendar') }}
),

cleaned AS (
    SELECT
        listing_id,
        date::DATE AS calendar_date,
        available AS is_available,
        TRY_CAST(REPLACE(REPLACE(price, '$', ''), ',', '') AS DECIMAL(10,2)) AS price,
        TRY_CAST(REPLACE(REPLACE(adjusted_price, '$', ''), ',', '') AS DECIMAL(10,2)) AS adjusted_price,
        minimum_nights::INT AS minimum_nights,
        maximum_nights::INT AS maximum_nights
    FROM source
)

SELECT * FROM cleaned
