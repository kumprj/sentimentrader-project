# SentimentTrader Application

## Overview
Collaborated with friend on an application that backtests stocks against an Optimism Index (known as Optix - data set and testing engine supplied by sentimentrader.com). This index uses 2200 custom-made indicators to compute the Optimism Index value - an integer 0 to 100. A number above 80 indicates extreme optimism, and a number below 20 indicates extreme pessimism. The custom-made indicators are updated daily, and we backtest any stocks/ETFs/commodities that fall into these extreme bands for the 10 day moving average.

Our Project
We wrote a Python script to automate loading the daily-updated indicators into an AWS PostgreSQL RDS. We then have a second Python script to identify which tickers fall into our extreme bands, and we backtest them. Our backtests tell us, at a high level, "when the ticker was at this Optix level in the past, here are the returns over 1/3/6/9/12 month periods." We can then use this information to make informed trade decisions, be it shares or options contracts.

Technology Stack - Python, Docker, Selenium, AWS Fargate, ECS, ECR, EC2, RDS, and S3.
* Daily Indicator Load - Python script, which grabs a .CSV off the internet, parses it, and inserts the indicator information into PostgreSQL table.
* Daily Backtest - Python script queries indicator table and returns list of tickers at both extremes. Script then loops through each ticker, testing it for historic returns and insert the results into PostgreSQL table. Tests are run using Selenium.
* Above scripts are run in a Docker Container - containerizing each script allow us to schedule and run these regularly in Fargate.
* NodeJS REST API using Serverless and AWS Lambda -> returns JSON to display on the website.
* Daily Email report using Python and AWS SES to alert us of any Stock Tickers that have >80% or <20% success rates. 

For more information on the infrastructure and architecture, see below.

# Setup and Use

The Application is structured into two components: daily indicator load and the backtesting script. This project is collaborated with [wellsjk](https://github.com/wellsjk). It requires a sentimentrader.com subscription and an AWS account.

## Set up a Database
We use an AWS RDS Postgres instance ([Setup Instructions](https://aws.amazon.com/getting-started/tutorials/create-connect-postgresql-db/)) for handling the data with this application. The default tutorial values are fine, but be sure to store them for later. Alternatively, any postgres database that you can connect to via psycopg2 should be fine. In the __sql_scripts__ folder we have the table creation scripts with your favorite database management tool. I use SQLWorkbench. 

You should now have:
* An AWS postgres db, with the connection information available in the RDS Console.
* Three tables created with the SQL Scripts. 

## Indicator Loading
Folder __src/sentimentrader_indicator_loading__ handles the acquisition of Sentimentrader.com's Indicators and stores them in the database. Action items in this folder include replacing __SentimenTraderDailyIndactor.py__'s database values with your values (if they differ), and updating __settings.yaml__ with your credential information. A template is supplied. Once those table values and credentials are supplied, we are all set. At a glance, the script:
* Acquires a CSV File of the Sentimentrader Indicators and downloads it to the container in the default location.
* Writes the indicator values to a stg table and prd table using Python csv/file parsing and a psycopg2 insert.

## Daily Backtest Script
__SentimenTraderBacktest.py__ in src/sentimentrader_backtest folder handles the backtests. One of these Indicators is called an Optimism Index (Optix). An optimism index exists for each of the S&P 1500 companies, as well as some commodities and ETFs. It is a somewhat secret creation of sentiment trader, but open for internal use. That is, we don't know how they calculate it, but we can know its value. We will use these Optimism Indexes to make trade decisions. We want to identify when an ETF, Commodity, etc. reaches an extreme level of optimism or pessimism (80 and 20 respectively to sentimentrader, but your mileage may vary). When a ticker reaches our low or high extreme, we add it to a list to be backtested and parse the backtest results. We are saying "backtest this ticker to show what the results were the last time it reached this Optix extreme." We are testing to see the 1/3/6/9/12 month returns historically and can then decide if the results are strong enough to go long or short. 

Specify your low and high extremes to your fitting and fill out your __settings.yaml__ elements. The database names will need to be updated to match yours. At a glance, this script:
* Queries our 'daily indicator' stg table to get the low and high extremes and creates a list of tickers. 
* Grab the Optix Name (i.e. SPY Optix), indicator name (SPY) and the last Optix close and enter them into three lists.
* Generate five URLs for each indicator. Say SPY is above our High Extreme of 80 - we want to see the returns at 1/3/6/9/12 months of SPY when it has reached this level. Another solution is to test for the exact optix value, instead of just above 80. Add the backtest URL to a list.
* Run through the list of backtests to run, and parse the results. Store this data into the database.

## Build the Container
Both scripts are run as containers on an Amazon Linux AMI. In the Dockerfile's for each, you can see we use an Amazon Linux AMI (similar to CentOS/RHEL). In the Dockerfile, we copy our necessary files to the linux container first, install miscellaneous software including python, and Google Chrome. We then run the backtest using Selenium. The Dockerfile does not need any modification.

Next, set up an ECR Repository - [Setup Instructions](https://console.aws.amazon.com/ecr/home). Name is arbitrary - our two are titled backtest_prd and dailyindicatorload.

CD to the directory of the Dockerfile (sentimentrader_backtest/) and build the dockerfile `docker build -t namehere:latest .`

Follow these steps to upload a docker image to ECR: [steps here](https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-ecr-image.html).

Repeat for the other Python script.

## Deploying the Application

Create an AWS ECS Task Definition - [Create an ECS Task Definition](https://console.aws.amazon.com/ecs/home?region=us-east-1#/taskDefinitions/create). Note this links takes you to US-East 1. Recommended to use the same region as your other Services. Specify Fargate and select the default ecs task role. Select one of your containers. We'll repeat these steps for the second container.

I allocated 0.5 GB and 0.25 vCPU for the daily indicator load, and 2GB and 0.5 vCPU for the backtest. For backtest I set a soft limit on the container of 750MiB and no hard limit. Soft Limit of 128 MiB for the daily indicator load container.

Next create your [AWS Fargate Cluster](https://aws.amazon.com/ecs/) and click Clusters on the left. Selet Networking Only and advance. Create a cluster name and leave VPC unchecked. Our Cluster uses the default VPC created with the Postgres Database. Click create. 

Click your fargate cluster and you will see a list of tabs. Tasks lets you run a container once, or you can utilize a scheduled task. We run the daily indicator load and the backtests every 6-8 hours, though the values are usually only updated daily.

# Using the Data
The whole purpose of this is to take the backtest results and use them to make educated trade decisions. How someone handles this data is very open ended. We have a simple boostrapped webpage that has pages by date, and shows the results (i.e. if SPY returned >5% for the next three observation periods). One can also add shorter and longer dated observation periods. We are displaying the results online. Additionally, we are emailing ourselves the extremely positive and extremely negative results every morning. Identifying these high and low success rate tickers are good for trading shares or options contracts with confidence.
