[out:json][timeout:180][maxsize:268435456];
(
 way["building"](45.416,12.306,45.456,12.368);
 relation["building"](45.416,12.306,45.456,12.368);
 way["natural"="coastline"](45.416,12.306,45.456,12.368);
 way["natural"="water"](45.416,12.306,45.456,12.368);
 relation["natural"="water"](45.416,12.306,45.456,12.368);
 way["waterway"~"^(canal|riverbank|river|dock)$"](45.416,12.306,45.456,12.368);
 relation["waterway"="riverbank"](45.416,12.306,45.456,12.368);
 way["place"~"^(island|islet)$"](45.416,12.306,45.456,12.368);
 relation["place"~"^(island|islet)$"](45.416,12.306,45.456,12.368);
 way["landuse"~"^(cemetery|grass|forest)$"](45.416,12.306,45.456,12.368);
 relation["landuse"="cemetery"](45.416,12.306,45.456,12.368);
 way["leisure"~"^(park|garden)$"](45.416,12.306,45.456,12.368);
 way["man_made"~"^(pier|breakwater)$"](45.416,12.306,45.456,12.368);
);
out geom;
