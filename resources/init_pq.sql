CREATE TABLE crossword_clue
(
    id       SERIAL       NOT NULL
        CONSTRAINT crossword_clue_pk
            PRIMARY KEY,
    user_id  VARCHAR(128) NOT NULL,
    question VARCHAR(128) NOT NULL,
    answers  JSON NOT NULL
);
