#!/usr/bin/env python

import csv
import time
from datetime import date
import os
import sys
import boto3
from botocore.exceptions import ClientError
from generate_email import generateListToEmail


def main():
    send_email()

def parseTickers(listOfTickers):
    resultingList = []
    splitNewLineList = listOfTickers.splitlines()

    # wrap lines in p tags for cleaner email reading
    for item in splitNewLineList:
        resultingList.append('<p>'+item+'</p>')
    
    return resultingList

def send_email():
    stringsToEmail =  generateListToEmail()
    stringsOnSeparateLines = "\n".join(stringsToEmail)

    SENDER = "..."
    RECIPIENT1 = "..."
    RECIPIENT2 = "..."
    AWS_REGION = "us-east-1"
    SUBJECT = "10 Day MA Daily Extreme Update"

    # non-HTML email clients body.
    BODY_TEXT = (f"{stringsOnSeparateLines}")
    
    # HTML body
    BODY_HTML = f"""<html>
    <head></head>
    <body>
        {parseTickers(stringsOnSeparateLines)}
    </body>
    </html>
        """

    CHARSET = "UTF-8"

    # Create a new SES resource and specify the region.
    client = boto3.client('ses',region_name=AWS_REGION)

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT1,RECIPIENT2
                ],
                
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML, # replace with contents to email
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )
    # Handle errors
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


if __name__ == '__main__':
    main()