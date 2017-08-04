# -*- coding: utf-8 -*-
import os
import environ

p = environ.Path(__file__) - 2
env = environ.Env()


def root(*paths, **kwargs):
    ensure = kwargs.pop('ensure', False)
    path = p(*paths, **kwargs)
    if ensure and not os.path.exists(path):
        os.makedirs(path)
    return path


def read_env():
    env_file = root('../.env')

    if os.path.exists(env_file):
        environ.Env.read_env(env_file)  # reading env file
