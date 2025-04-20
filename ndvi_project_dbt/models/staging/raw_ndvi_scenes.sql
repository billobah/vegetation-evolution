-- Source brute connectée à la table standardized_ndvi dans le schéma main
SELECT
    scene_id,
    ndvi_array,
    width,
    height
FROM {{ source('raw', 'standardized_ndvi') }}
