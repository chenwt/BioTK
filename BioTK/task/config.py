import lz4
from kombu import Exchange, Queue
from kombu.common import Broadcast
import kombu.compression

from BioTK import CONFIG

BROKER_URL = CONFIG["celery.broker.url"]

CELERY_RESULT_BACKEND = "redis://%s:%s/%s" % (
        CONFIG["redis.host"],
        CONFIG["redis.port"],
        int(CONFIG["redis.result_store.index"]))

CELERY_IMPORTS = (
        "BioTK.db.load",
)
CELERY_WORKER_DIRECT = True

# Queues and routes

queue = CONFIG["celery.queue"]
exchange = CELERY_DEFAULT_EXCHANGE = Exchange(queue)
CELERY_QUEUES=(
    Queue(queue, Exchange(queue), routing_key=queue),
)
CELERY_DEFAULT_QUEUE=queue

# Compression and serialization

CELERY_ACCEPT_CONTENT = ["pickle", "msgpack"]
kombu.compression.register(lz4.dumps, lz4.loads, 
    "application/octet-stream", aliases=["lz4"])
CELERY_MESSAGE_COMPRESSION="lz4"

for k,v in CONFIG.items():
    if k.startswith("celery.cfg."):
        k = k.split(".")[2].upper()
        if v.strip() == "True":
            v = True
        elif v.strip() == "False":
            v = False
        else:
            if "," in v:
                v = v.split(",")
        globals()[k] = v
