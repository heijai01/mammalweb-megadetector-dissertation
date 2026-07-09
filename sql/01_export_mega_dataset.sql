SELECT
    p.photo_id,
    p.sequence_id,
    p.sequence_num,
    p.contains_human,
    p.status,
    p.filename,
    p.dirname,
    COALESCE(MAX(CASE WHEN c.species_id = 87 THEN c.prob END), 0) AS mega_human_confidence,
    COALESCE(MAX(CASE WHEN c.species_id = 2077 THEN c.prob END), 0) AS mega_animal_confidence,
    COALESCE(MAX(CASE WHEN c.species_id = 2049 THEN c.prob END), 0) AS mega_vehicle_confidence
FROM Classify c
JOIN Photo p
    ON p.photo_id = c.photo_id
WHERE
    c.origin = 'MEGA'
    AND p.status = 1
    AND p.photo_id BETWEEN X AND Y
GROUP BY
    p.photo_id,
    p.sequence_id,
    p.sequence_num,
    p.contains_human,
    p.status,
    p.filename,
    p.dirname
ORDER BY
    p.photo_id;
