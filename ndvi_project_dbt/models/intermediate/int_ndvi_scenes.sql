with base as (
    select *
    from {{ ref('raw_ndvi_scenes') }}
)

select
    scene_id,
    ndvi_array,
    width,
    height,
    cast(substring(SPLIT_PART(scene_id, '_', 4), 1, 8) as date) as acquisition_date
from base