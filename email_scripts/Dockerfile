FROM python:3.7

WORKDIR /usr/local/bin

COPY requirements.txt .
COPY generate_email.py .
COPY send_email.py .


# RUN yum -y install python37-pip \  
#     && yum clean all

RUN cat requirements.txt | xargs -n 1 python3 -m pip install

ARG aws_id=default_value
ENV AWS_ACCESS_KEY_ID=$aws_id

ARG aws_key=default_value
ENV AWS_SECRET_ACCESS_KEY=$aws_key

CMD python3 send_email.py