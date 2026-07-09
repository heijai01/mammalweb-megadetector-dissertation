SELECT
    p.photo_id,
    p.site_id,
    p.taken,
    s.site_name,
    s.latitude,
    s.longitude,
    c.species_id,
    c.prob,
    c.xmin,
    c.ymin,
    c.xmax,
    c.ymax
FROM Classify c
JOIN Photo p
    ON p.photo_id = c.photo_id
LEFT JOIN Site s
    ON p.site_id = s.site_id
WHERE
    c.origin = 'MEGA'
    AND c.species_id IN (87, 2077, 2049)
    AND p.status = 1
    AND p.photo_id BETWEEN X AND Y
ORDER BY
    p.photo_id,
    c.species_id,
    c.prob DESC;
