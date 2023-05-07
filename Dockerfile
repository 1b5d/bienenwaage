FROM acockburn/appdaemon:4.2.1

COPY ./appdaemon/appdaemon.yaml /conf/
COPY ./appdaemon/requirements.txt /conf/
COPY ./appdaemon/system_packages.txt /conf/
COPY ./appdaemon/apps.yaml /conf/apps/
COPY ./appdaemon/hx711.py /conf/apps/
COPY ./appdaemon/bienenwaage.py /conf/apps/
COPY ./appdaemon/display.py /conf/apps/
