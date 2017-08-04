#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    from hubot.settings import read_env
    read_env()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hubot.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
