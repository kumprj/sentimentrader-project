# Daily Email Alerts

This section of code sends a daily email update to our inboxes, outlining tickers at extreme edge cases that we might care to look at. We offer a front-end
as well. This is to highlight some of the truly extreme scenarios.

Boto requires aws cli to be configured, so we're passing those credentials as environment variables for the time being. Run in Fargate or your favorite container management service. 

To run this script, build the Dockerfile with the two environment variables mentioned above. In send_email.py's send_email method, replace the url with your rest api endpoint that returns json. Additionally, update the sender and recipients with email addresses verified on your AWS SES. I scheduled it using a cron expression in Fargate to send to myself every day Mon-Fri at 6am. 