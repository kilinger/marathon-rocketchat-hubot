# -*- coding: utf-8 -*-
import hashlib
import json
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from projects.models import ProjectBuild, ProjectRelease
from projects.tasks import release_deploy


logger = logging.getLogger('hubot')


@csrf_exempt
@require_POST
def build_notify(request):

    t = request.GET.get("t", "")
    code = request.GET.get("code", "")
    code_calculate = hashlib.md5("{0}{1}".format(settings.SECRET_KEY, str(t))).hexdigest()
    if code != code_calculate:
        return HttpResponse("Failed", status=400)

    try:
        data = json.loads(request.body)
    except:
        return HttpResponse("Failed", status=400)
    task_id = data.get("task_id", "")
    status = data.get("status", "")
    try:
        build = ProjectBuild.objects.get(task_id=task_id)
    except ProjectBuild.DoesNotExist as e:
        logger.error(str(e))
        return HttpResponse("Failed", status=400)
    if status:
        status = status[5:].capitalize()  # TASK_FINISHED -> Finished
        build.status = status
        build.save()

        release = ProjectRelease.objects.get_or_create(build=build)[0]
        if build.is_success():
            release_deploy.apply_async(args=[release.id, False, True, 5])
        else:
            release.mark_failed()
        return HttpResponse("Success")

    return HttpResponse("Failed", status=400)
