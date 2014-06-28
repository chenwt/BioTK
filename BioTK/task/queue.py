from celery import Celery
QUEUE = Celery("BioTK")
QUEUE.config_from_object("BioTK.task.config")

from .etc import *
from .region import *
from .graph import *
