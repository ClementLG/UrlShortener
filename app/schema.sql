DROP TABLE IF EXISTS urls;
CREATE TABLE urls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  short_code TEXT UNIQUE NOT NULL,
  long_url TEXT NOT NULL
);