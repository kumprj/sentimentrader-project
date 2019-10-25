DROP TABLE IF EXISTS "dailyIndicatorSTG" CASCADE;

CREATE TABLE "dailyIndicatorSTG"
(
   name             varchar,
   indicator        varchar,
   last_close       varchar,
   update_date      date,
   sentiment_value  varchar
);

COMMIT;
