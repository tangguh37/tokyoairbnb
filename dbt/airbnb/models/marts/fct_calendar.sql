{{ config(
    materialized='incremental',
    incremental_strategy='append',
    unique_key='cal_key',
    on_schema_change='fail'
) }}

WITH calendar AS (
    SELECT * FROM {{ ref('stg_calendar') }}
)

SELECT
    *,
    CAST(listing_id AS VARCHAR) || '-' || CAST(calendar_date AS VARCHAR) AS cal_key
FROM calendar

{% if is_incremental() %}
WHERE (listing_id, calendar_date) NOT IN (
    SELECT listing_id, calendar_date FROM {{ this }}
)
{% endif %}
