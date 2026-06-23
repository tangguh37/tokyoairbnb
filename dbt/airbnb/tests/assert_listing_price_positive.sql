SELECT listing_id, price
FROM {{ ref('dim_listing') }}
WHERE price <= 0
