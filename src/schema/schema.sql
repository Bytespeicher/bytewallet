DROP TABLE IF EXISTS wallet;
CREATE TABLE wallet (
  id          INTEGER   PRIMARY KEY AUTOINCREMENT,
  name        TEXT      UNIQUE,
  money       INTEGER   DEFAULT 0,
  pin         TEXT      NOT NULL,
  photo       TEXT      NOT NULL,
  last_update DATETIME  DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS config;
CREATE TABLE config (
  name      TEXT    PRIMARY KEY,
  value     TEXT
);

INSERT OR REPLACE INTO config (name, value) VALUES ('dbversion', '1');
