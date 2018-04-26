-- Podcasts state db.

-- Podcast channel.
CREATE TABLE podcast (
	podcastid	INTEGER	PRIMARY KEY,
	title		TEXT	UNIQUE,
	rssurl		TEXT	UNIQUE,
	description	TEXT,
	homepage	TEXT
);

-- Podcast episode. Favour regular rss, but also include media: and itunes: info if needed.
CREATE TABLE episode (
	episodeid	INTEGER	PRIMARY KEY,
	podcastid	INTEGER	REFERENCES podcast,
	guid		TEXT	UNIQUE,
	permalink	BOOLEAN,
	mediaurl	TEXT,
	mediatype	TEXT,
	medialength	INTEGER,
	title		TEXT,
	description	TEXT,
	link		TEXT,
	pubdate		INTEGER
);

-- Global app/general configuration.
CREATE TABLE config (
	key		TEXT PRIMARY KEY,
	value		TEXT,
        description	TEXT
);

-- Global config options, and their defaults.
INSERT INTO config ('key', 'value', 'description') VALUES ('downloaddir', '~/scoop', 'Base podcast download directory');
INSERT INTO config ('key', 'value', 'description') VALUES ('saverss', '1', 'Set to 1 if the rss file should be saved to the download directory');
INSERT INTO config ('key', 'value', 'description') VALUES ('schemaversion', '1', 'Scoop sqlite schema interface version number');
INSERT INTO config ('key', 'value', 'description') VALUES ('useragent', 'Scoop/0.1', 'HTTP User Agent');

-- Work queue for downloading episodes.
CREATE TABLE dl (
	dlid		INTEGER PRIMARY KEY,
	episodeid	INTEGER REFERENCES episode,
	status		TEXT,		-- one of 'w' waiting, 's' skipped, 'd' downloaded, 'e' error retrieving.
	added		INTEGER,	-- when the episode was discovered.
        actioned	INTEGER,	-- when the episode was downloaded, skipped, or errored.
        filename	TEXT,		-- destination filename (only) for saved media file.
        CHECK		(status IN ('d', 'e', 's', 'w'))
);
