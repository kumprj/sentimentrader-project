FROM amazonlinux:latest

COPY requirements.txt /home/requirements.txt
COPY SentimentTraderDailyIndicator.py /home/SentimentTraderDailyIndicator.py
COPY settings.yaml /home/settings.yaml
COPY credentials.py /home/credentials.py

RUN yum -y install git \
    python2 \
    python2-pip \  
    zip \
    unzip \ 
    wget \ 
    Xvfb \
    && yum clean all

RUN cat /home/requirements.txt | xargs -n 1 python2 -m pip install

# Install Chrome dependencies
RUN yum install -y pango.x86_64 libXcomposite.x86_64 libXcursor.x86_64 \
    libXdamage.x86_64 libXext.x86_64 libXi.x86_64 libXtst.x86_64 \
    cups-libs.x86_64 libXScrnSaver.x86_64 libXrandr.x86_64 GConf2.x86_64 \
    alsa-lib.x86_64 atk.x86_64 gtk3.x86_64 ipa-gothic-fonts xorg-x11-fonts-100dpi \
    xorg-x11-fonts-75dpi xorg-x11-utils xorg-x11-fonts-cyrillic xorg-x11-fonts-Type1 xorg-x11-fonts-misc

RUN cd /tmp && wget https://chromedriver.storage.googleapis.com/77.0.3865.40/chromedriver_linux64.zip && unzip chromedriver_linux64.zip \ 
    && rm -f chromedriver_linux64.zip && mv chromedriver /usr/bin/chromedriver

RUN curl https://intoli.com/install-google-chrome.sh | bash && mv /usr/bin/google-chrome-stable /usr/bin/google-chrome && rm -rf /var/cache/yum

CMD python2 /home/SentimentTraderDailyIndicator.py