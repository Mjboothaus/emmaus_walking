select
    date,
    latitude,
    longitude,
    altitude,
    workout_id
from
    workout_points
group by
    workout_id
order by
    date desc
