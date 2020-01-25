FROM python:3

ADD requirements.txt /
ADD install-coap-client.sh /
RUN sudo sh install-coap-client.sh
RUN pip install -r requirements.txt
ADD *.py /

CMD [ "python", "./main.py" ]
