with base as (
    select *
    from {{ ref('int_ndvi_scenes') }}
),

unnested as (
    select
        b.scene_id,
        b.acquisition_date,
        b.width,
        b.height,
        i as pixel_index,
        b.ndvi_array[i] as ndvi_value
    from base b,
         range(1, array_length(b.ndvi_array) + 1) as t(i)
)

select
    scene_id,
    acquisition_date,
    pixel_index,
    ndvi_value
from unnested
