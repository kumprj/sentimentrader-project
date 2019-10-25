DROP TABLE IF EXISTS indicatorprd CASCADE;

CREATE TABLE indicatorprd
(
   indicator  varchar(100)   NOT NULL,
   value      varchar        NOT NULL,
   date       date           NOT NULL
);

COMMIT;
