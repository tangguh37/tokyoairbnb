{{ config(
    materialized='incremental',
    incremental_strategy='append',
    unique_key='review_id',
    on_schema_change='fail'
) }}

WITH reviews AS (
    SELECT * FROM {{ ref('stg_reviews') }}
)

{% if is_incremental() %}
SELECT r.*
FROM reviews r
LEFT JOIN {{ this }} t ON r.review_id = t.review_id
WHERE t.review_id IS NULL
{% else %}
SELECT * FROM reviews
{% endif %}
