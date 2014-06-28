import lz4
from kombu import Exchange, Queue
from kombu.common import Broadcast
import kombu.compression

from BioTK import CONFIG

redis_base_uri = "redis://%s:%s" % (
        CONFIG["redis.host"],
        CONFIG["redis.port"])
#broker_uri = "%s/%s" % (
#        redis_base_uri,
#        int(CONFIG["redis.task_queue.index"]))

BROKER_URL = "amqp://"
CELERY_RESULT_BACKEND = "%s/%s" % (
        redis_base_uri,
        int(CONFIG["redis.result_store.index"]))

CELERY_IMPORTS = (
        "BioTK.task.etc",
        "BioTK.task.graph.load",
        "BioTK.task.region"
)
CELERY_WORKER_DIRECT = True

# Queues and routes

exchange = CELERY_DEFAULT_EXCHANGE = Exchange('default')
CELERY_QUEUES=(
    Queue('default', Exchange('default'), routing_key='default'),
)
CELERY_DEFAULT_QUEUE="default"

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
