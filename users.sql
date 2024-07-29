-- CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, firstname TEXT NOT NULL, lastname TEXT NOT NULL);
-- CREATE TABLE information (
--     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
--     user_id INTEGER NOT NULL,
--     intro TEXT,
--     skills TEXT,
--     projects TEXT,
--     FOREIGN KEY (user_id) REFERENCES users (id)
-- );
SELECT * FROM information;