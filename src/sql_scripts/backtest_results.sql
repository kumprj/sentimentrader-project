DROP TABLE IF EXISTS backtest_results CASCADE;

CREATE TABLE backtest_results
(
   symbol               varchar(20)   NOT NULL,
   indicator            varchar(40)   NOT NULL,
   lookback_period      varchar(25),
   observation_period   varchar(20)   NOT NULL,
   index_filter         varchar(50),
   indicator_smoothing  varchar(50),
   test_start_date      varchar(10),
   test_end_date        varchar(10),
   exclude_overlapping  varchar(15),
   index_filter_swap    varchar(15),
   indicator_level      varchar(15),
   market_environment   varchar(50),
   index_ma_slope       varchar(15),
   total_return         varchar(15),
   avg_return           varchar(15),
   z_score              varchar(10),
   buy_hold_return      varchar(15),
   win_rate             varchar(15),
   avg_win              varchar(15),
   avg_loss             varchar(15),
   max_risk             varchar(15),
   total_trades         varchar(15),
   total_pos            varchar(15),
   total_neg            varchar(15),
   time_in_mkt          varchar(15),
   todays_date          varchar(15)   NOT NULL
);

ALTER TABLE backtest_results
   ADD CONSTRAINT backtest_results_indicator_observation_period_todays_da_key UNIQUE (indicator, observation_period, todays_date);



COMMIT;
