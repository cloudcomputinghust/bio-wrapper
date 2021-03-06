#
# Copyright 2016 - Nguyen Quang "TechBK" Binh.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from aiohttp import web
from managers import SwiftManager, Job
import json
import asyncio


def handle_errors(func):
    """

    :param func:
    :return:
    """
    def wrapped(s, request):
        """
        :param s:
        :param request:
        :return:
        """

        try:
            data = yield from func(s, request)
            return data
        except Exception as e:
            message = "%s: %s" % (type(e).__name__, e)
            data = {
                'status': False,
                'error_message': message
            }
            return web.Response(body=json.dumps(data).encode('utf-8'))

    return wrapped


class JobsHandler(object):
    def __init__(self, loop):
        self.loop = loop
        self.list_of_job = {}
        self._taskid = 0

    def _get_job_id(self):
        self._taskid += 1
        return str(self._taskid)

    @handle_errors
    @asyncio.coroutine
    def runtask(self, request):
        """
        POST method with payload:
        - user
        - key
        - tenant
        - authurl
        - cm: commandline shell
        - input_file: if None, swift not get data
        - output_file: if None, swift not put data
        :param aiohttp.web.Request request: require user, key, tenant, authurl, input_file, output_file, cm
        :return: aiohttp.web.Response: string job_id
        """
        yield from request.post()
        user = request.POST['user']
        key = request.POST['key']
        tenant = request.POST['tenant']
        authurl = request.POST['authurl']
        cm = request.POST['cm']
        input_file = request.POST.get('input_file')  #if Null return None
        output_file = request.POST.get('output_file')   #if Null return None

        # if not input_file and '%(input_file)s' in cm:
        #     raise Exception("Commandline Syntax Error: if not input_file and '%(input_file)s' in cm")
        #
        # if input_file and not '%(input_file)s' in cm:
        #     raise Exception("Commandline Syntax Error: if input_file and not '%(input_file)s' in cm")
        #
        # if not output_file and '%(output_file)s' in cm:
        #     raise Exception("Commandline Syntax Error: if not output_file and '%(output_file)s' in cm")

        swift = SwiftManager(user=user,
                             key=key,
                             tenant=tenant,
                             authurl=authurl,
                             input_file=input_file,
                             output_file=output_file,
                             directory=self._get_job_id(),
                             )

        job = Job(swift, cm)

        self.list_of_job[str(self._taskid)] = job
        data = {
            'status': True,
            'job_id': str(self._taskid),
        }
        return web.Response(body=json.dumps(data).encode('utf-8'))

    @handle_errors
    @asyncio.coroutine
    def listjobs(self, request):
        """
        GET method
        :param aiohttp.web.Request request: no requirement
        :return:
        """
        data = {
            'empty': False,
            'jobs': [key for key in self.list_of_job.keys()],
            'status': True
        }
        return web.Response(body=json.dumps(data).encode('utf-8'))

    @handle_errors
    @asyncio.coroutine
    def job(self, request):
        """
        GET method with payload:
        - job_id
        :param aiohttp.web.Request request: required job_id
        :return:
        """

        job_id = request.GET['job_id']
        job = self.list_of_job[job_id]
        is_done = job.process.done()
        if is_done:
            # try:
                out = yield from job.process
                data = {
                    'job_id': job_id,
                    'job_done': job.process.done(),
                    'job_error': job.error,
                    'process_out': out.decode('utf-8'),
                    # 'process_error': error.decode('utf-8'),
                    'status': True
                }
            # except Exception as e:
            #     message = "%s: %s" % (type(e).__name__, e)
            #     data = {
            #         'job_id': job_id,
            #         'job_done': job.process.done(),
            #         'job_error': job.error,
            #         'error_message': message,
            #         'status': True
            #     }
        else:
            data = {
                    'job_id': job_id,
                    'job_done': job.process.done(),
                    'job_error': job.error,
                    'status': True
            }
        return web.Response(body=json.dumps(data).encode('utf-8'))

    @handle_errors
    @asyncio.coroutine
    def canceljob(self, request):
        """
        POST method with payload:
        - job_id
        If prevstatus = True -> job is running, else job is already done.
        :param aiohttp.web.Request request: require job_id
        :return:
        """
        yield from request.post()
        job_id = request.POST['job_id']
        job = self.list_of_job[job_id]
        prevstatus = job.process.cancel()
        data = {
            'prevstatus': prevstatus,
            'job_id': job_id,
            'status': True,
        }

        return web.Response(body=json.dumps(data).encode('utf-8'))
