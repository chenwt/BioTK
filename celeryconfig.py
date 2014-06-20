import socket

CELERY_ENABLE_UTC = True
CELERY_ACCEPT_CONTENT = ["pickle", "msgpack"]
CELERY_TIMEZONE = "US/Chicago"

if socket.gethostname() == "phoenix":
    BROKER_URL = CELERY_RESULT_BACKEND = "amqp://"
else:
    BROKER_URL = CELERY_RESULT_BACKEND = "redis://10.77.77.1/"
