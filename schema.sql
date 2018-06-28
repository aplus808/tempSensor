DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS temperatures;
DROP TABLE IF EXISTS camera;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE temperatures (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME,
  tempc NUMERIC,
  tempf NUMERIC
);

CREATE TABLE camera (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME,
  content_type TEXT,
  filename TEXT,
  filepath TEXT,
  iso NUMERIC,
  resolution TEXT,
  framerate NUMERIC,
  framerate_range TEXT,
  sensor_mode NUMERIC,
  active NUMERIC
);