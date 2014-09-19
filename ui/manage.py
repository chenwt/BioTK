#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    for app in os.listdir("apps"):
        path = os.path.join("apps", app)
        sys.path.append(path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "btkui.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
