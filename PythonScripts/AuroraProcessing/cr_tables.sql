DROP TABLE IF EXISTS auroraStrength;

CREATE TABLE auroraStrength(
	id int,
	obs_date timestamptz,
	forecast timestamptz,
	strength numeric,
	geom geography
);

