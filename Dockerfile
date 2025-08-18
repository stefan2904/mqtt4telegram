FROM python:3

RUN apt update \
	&& apt install libssl3 libssl-dev \
	&& apt autoremove && apt autoclean

ADD requirements.txt /
ADD tools/install-coap-client.sh /
RUN sh install-coap-client.sh
RUN pip install -r requirements.txt
ADD *.py /

CMD [ "python", "./main.py" ]
