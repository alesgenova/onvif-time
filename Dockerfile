FROM python:3.12-alpine

LABEL org.opencontainers.image.source=https://github.com/alesgenova/onvif-time
LABEL org.opencontainers.image.description="Periodically set cameras time through ONVIF."
LABEL org.opencontainers.image.licenses=MIT

RUN pip install --no-cache-dir ntplib onvif_zeep

COPY src/main.sh /src/main.sh
COPY src/onvif_time.py /src/onvif_time.py
COPY src/config.json /config/config.json
RUN chmod +x /src/main.sh

ENV ONVIF_TIME_SCHEDULE=${ONVIF_TIME_SCHEDULE:-"0  2  *  *  *"}
ENV ONVIF_TIME_STARTUP_SYNC=${ONVIF_TIME_STARTUP_SYNC:-"true"}
ENV ONVIF_TIME_DRY_RUN=${ONVIF_TIME_DRY_RUN:-"false"}

CMD ["/src/main.sh"]
