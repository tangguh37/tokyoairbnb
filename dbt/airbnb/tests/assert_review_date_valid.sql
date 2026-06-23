SELECT review_id, review_date
FROM {{ ref('fct_reviews') }}
WHERE review_date > CURRENT_DATE
   OR review_date < '2010-01-01'
