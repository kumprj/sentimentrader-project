# Daily Email Alerts

This section of code sends a daily email update to our inboxes, outlining tickers at extreme edge cases that we might care to look at. We offer a front-end
as well. This is to highlight some of the truly extreme scenarios.

Boto requires aws cli to be configured, so we're passing those credentials as environment variables for the time being. Run in Fargate or your favorite container management service. 