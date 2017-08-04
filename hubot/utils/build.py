# -*- coding: utf-8 -*-
import hashlib
import json
import time

import requests
from django.conf import settings

from api.utils import logger


def build_code_to_docker(image_name, git_repo, git_tag, git_id_rsa):
    t = int(time.time())
    code = hashlib.md5("{0}{1}".format(settings.SECRET_KEY, str(t))).hexdigest()
    url = settings.BUILD_CALLBACK_URI + "?t={0}&code={1}".format(t, code)

    context = {
        'timestamp': t
    }

    volumes = []
    for volume in settings.BUILD_VOLUMES.split(","):
        parts = [e.strip() for e in volume.split(":")]

        if len(parts) not in [2, 3]:
            continue

        host_path = parts[0].format(**context)
        container_path = parts[1].format(**context)

        v = {"host_path": host_path, "container_path": container_path}

        if len(parts) == 3:
            mode = parts[2].upper()
            if mode in ['RO', 'RW']:
                v["mode"] = mode

        volumes.append(v)

    envs = {
        "IMAGE_NAME": image_name,
        "GIT_REPO": git_repo,
        "GIT_TAG": git_tag,
        "GIT_ID_RSA": git_id_rsa
    }
    for env in settings.BUILD_ENVS.split(","):
        key, value = env.split("=", 1)
        envs.update(**{key: value})

    data = {
        "task_cpus": 1.0,
        "task_mem": 1024.0,
        "docker_image": "index.xxxxx.com/builder",
        "docker_privileged": True,
        "command": "/usr/local/bin/dind /run.sh",
        "volumes": volumes,
        "callback_uri": url,
        "env": envs,
        "uris": [
            "file:///etc/docker.tar.gz"
        ]
    }
    url = settings.EREMETIC_URL
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers,
                                 auth=(settings.EREMETIC_USERNAME, settings.EREMETIC_PASSWORD))
    except Exception as e:
        logger.error(str(e))
        return False, str(e)
    return True, response.json()
