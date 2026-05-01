FROM apache/nifi:latest
USER root
RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install pydantic==2.6.0 psycopg2-binary==2.9.9 elasticsearch==8.11.0 --break-system-packages || pip3 install pydantic==2.6.0 psycopg2-binary==2.9.9 elasticsearch==8.11.0
USER nifi