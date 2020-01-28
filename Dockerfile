FROM python:3

ADD requirements.txt /
ADD tools/install-coap-client.sh /
RUN sh install-coap-client.sh
RUN pip install -r requirements.txt
ADD *.py /

CMD [ "python", "./main.py" ]
