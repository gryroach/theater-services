query = """
SELECT
    fw.id,
    fw.title,
    fw.description,
    fw.rating as imdb_rating,
    COALESCE (array_agg(DISTINCT p.full_name) FILTER (WHERE pfw.role='director'),'{}') as directors_names,
    COALESCE (array_agg(DISTINCT p.full_name) FILTER (WHERE pfw.role='actor'),'{}') as actors_names, 
    COALESCE (array_agg(DISTINCT p.full_name) FILTER (WHERE pfw.role='writer'),'{}') as writers_names,  
    COALESCE (
        json_agg(
            DISTINCT jsonb_build_object(
                'id', p.id,
                'name', p.full_name
            )
        ) FILTER (WHERE p.id is not null and pfw.role='director'),
        '[]'
    ) as directors,
    COALESCE (
        json_agg(
            DISTINCT jsonb_build_object(
                'id', p.id,
                'name', p.full_name
            )
        ) FILTER (WHERE p.id is not null and pfw.role='actor'),
        '[]'
    ) as actors,
    COALESCE (
        json_agg(
            DISTINCT jsonb_build_object(
                'id', p.id,
                'name', p.full_name
            )
        ) FILTER (WHERE p.id is not null and pfw.role='writer'),
        '[]'
    ) as writers,
    array_agg(DISTINCT g.name) as genres,
    greatest(MAX(fw.modified), MAX(g.modified), MAX(p.modified)) as last_modified_date
FROM content.film_work fw
LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
LEFT JOIN content.person p ON p.id = pfw.person_id
LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
LEFT JOIN content.genre g ON g.id = gfw.genre_id
GROUP BY fw.id
HAVING greatest(MAX(fw.modified), MAX(g.modified), MAX(p.modified)) > %s
ORDER BY fw.modified
"""