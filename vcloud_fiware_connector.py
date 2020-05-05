# vcloud_fiware_connector
# v1.0, 2020-04-26, RTG, Vibrobox

"""

название:
vcloud_fiware_connector или vweb_fiware_connector

назначение:
связать веб-платформу вибробокс с компонентами фивара,
для начала - достаточно контекст брокера (КБ)

задачи сервиса:
1. Получать обновлениея от КБ о приходе новых данных
2. Отправка собщений через vbot о новых данных и предварительных выводах
(3. Проверка доступности данных для скачивания и пригодности обработки - другой сервис?)
4. Создание запроса на обработку новых данных
5. Получение обносления о завершении обрабоботки (от нашего веба?)
6. Обнавление метаинфы сслыкаим на данные, результаты обработки, итоговые выводы.
7. Отправка собщений через vbot о завершении обработки и итоговых выводах.

упрощенная схема (для демки) - пп. 1, 6, 2.
"""


# libs import from Vibrobox bot
import os, sys, shutil, time
import logging
import ssl
import requests
import asyncio
from aiohttp import web, ClientSession
import aiohttp_cors
import json
import configparser


# libs import from vbox_fiware_connector
import os, sys
from vbxlib.fiware_requests import *
from vbxlib.network import ping_port as ping_port


###
import threading

import re

class vcloud_fiware_connector():

    def __init__(self, cfg_path=None):

        # SET CONFIG AND DEFAULT SETTINGS 
        self.db_host = os.environ['MONGODB_HOST'] # mongo database
        self.db_port = os.environ['MONGODB_PORT'] # mongo database
        self.cb_host = os.environ['CONTEXT_BROKER_HOST'] # orion context broker
        self.cb_port = os.environ['CONTEXT_BROKER_PORT'] # orion context broker
        self.dr_host = os.environ['DRACO_HOST'] # draco (preserves history)
        self.dr_port = os.environ['DRACO_PORT0'] # draco (preserves history)
        self.iota_host = os.environ['IOT_AGENT_HOST'] # iot-agent (mqtt+json to ngsi converter)
        self.iota_port0 = os.environ['IOT_AGENT_PORT0'] # iot-agent (mqtt+json to ngsi converter)
        self.iota_port1 = os.environ['IOT_AGENT_PORT1'] # iot-agent (mqtt+json to ngsi converter)
        self.vbot_host = os.environ['VBOT_HOST'] # vibrobox bot service
        self.vbot_port = os.environ['VBOT_PORT0'] # vibrobox bot service

        self.vbot_api_token = os.environ['VBOT_API_TOKEN'] # vibrobox bot api key
        self.vbot_tg_api_token = os.environ['VBOT_TG_API_TOKEN'] # telegram bot api key for notifications
        self.vbot_tg_chat_id = os.environ['VBOT_TG_CHAT_ID'] # telegram chat id for notifications
        self.vcloud_fc_port = os.environ['VCLOUD_FC_PORT']
        self.root_dir = '.'
        self.data_dir = '.'
        self.data_types = ['.wav', '.wav.bz2', '.tar.bz2']
        self.cfg_name = 'vbox_fc_cfg.json'
        self.log_name = 'vbox_fc_log.txt'
        self.meta_name = 'vbox_fc_meta.json'

        # PARSE INPUT ARGS
        def wavs_are_in_start_args():
            print('DEBUG: sys.argv == {}'.format(sys.argv))
            return any(arg.endswith(ext) 
                       for arg in sys.argv 
                       for ext in self.data_types)

        self.test_mode = True or '--test' in sys.argv
        self.debug_mode = True or '--debug' in sys.argv
        self.ping_hosts = False or '--ping' in sys.argv
        self.subscribe = False or  '--subscribe' in sys.argv
        self.server_mode = (True or '--server' in sys.argv) and not'--no_server' in sys.argv


        # ADD SERVER ROUTES
        vcloud_fc_web_app = web.Application()
        vcloud_fc_web_app.router.add_route('POST', '/api/v1/notify', self.hello)
        vcloud_fc_web_app.router.add_get('/hello', self.hello)
        vcloud_fc_web_app.router.add_post('/{token}/', self.hello)
        vcloud_fc_web_app.router.add_post('/ping', self.ping_remotes_a)
        vcloud_fc_web_app.router.add_post('/subscribe', self.set_subscription_a)

        # ALLOW ADDITIONAL MIME-TYPES
        # To request resources with custom headers (e.g. "Content-Type"="application/json")
        # or using custom HTTP methods (e.g. PUT, DELETE) that are not allowed by SOP,
        # CORS-enabled browser first send preflight request to the resource using OPTIONS method,
        # in which he queries access to the resource with specific method and headers
        # Configure default CORS settings.
        cors = aiohttp_cors.setup(vcloud_fc_web_app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                )
        })
        # Configure CORS on all routes.
        for route in list(vcloud_fc_web_app.router.routes()):
            cors.add(route)

        # CREATE MAIN PROGRAM ASYNC LOOP
        self.loop = asyncio.get_event_loop()
        self.vcloud_fc_runner = web.AppRunner(vcloud_fc_web_app)
        self.loop.run_until_complete(self.vcloud_fc_runner.setup())
        self.vcloud_fc_server = web.TCPSite(self.vcloud_fc_runner, port=self.vcloud_fc_port)
        self.loop.run_until_complete(self.vcloud_fc_server.start())

    
    def start_server(self):
        try:
            async_loop_thread = threading.Thread(target=self.loop.run_forever)
            async_loop_thread.start()

            print("Main program loop started (Press CTRL+C to quit)")
            import time
            while True:
                # the time reduce cpu usage of main thread, has no impact on finish time
                time.sleep(30)
        except KeyboardInterrupt:
            # someone pressed ctr+c
            print('Inrerrupted by keyboard (Ctrl+C)!')
        except Exception as e:
            # someone pressed ctr+c
            print('EXCEPTION: {}'.format(e))
        finally:
            # self.vcloud_fc_runner.cleanup()
            self.loop.call_soon_threadsafe(self.loop.stop)
            async_loop_thread.join(timeout=3) # the timeout has no impact on finish time, it takes 8 sec on test server
    
    def ping_remotes(self):

        print('\nINFO: checking fiware components...\n')

        ping_port(self.db_host, self.db_port)
        ping_port(self.cb_host, self.cb_port)
        ping_port(self.dr_host, self.dr_port)
        ping_port(self.iota_host, self.iota_port0)
        
        fiware_check_database(self.db_host, self.db_port);
        fiware_check_cbroker(self.cb_host, self.cb_port);
        fiware_check_draco(self.dr_host, self.dr_port);
        fiware_check_iotagent(self.iota_host, self.iota_port0);

    def set_subscription(self):
    
        fiware_set_subscription_for_vcloud_fc(self.cb_host, self.cb_port);
        fiware_get_subscriptions(self.cb_host, self.cb_port);

    async def ping_remotes_a(self, request):
        self.ping_remotes()
        return web.Response(text='Pinging completed.')
    async def set_subscription_a(self, request):
        self.set_subscription()
        return web.Response(text='Subscribing completed.')


    # Test the server is running by /hello url
    async def hello(self, request):
        greeting = 'vcloud_fc: Hello, World!'
        print('Request: {}'.format(request.rel_url.human_repr()))
        print('Headers: {}'.format(["{}:{}".format(k,v) for k,v in request.headers.items()]))
        if 'Content-Type' in request.headers \
                and 'application/json' in request.headers['Content-Type']:
            request_body_dict = await request.json()

            texts = [
                request_body_dict['data'][0]['Record time']['value'],
                request_body_dict['data'][0]['Record time']['type'],
                request_body_dict['data'][0]['File id']['value'],
                request_body_dict['data'][0]['File id']['type'],
                request_body_dict['data'][0]['File name']['value'],
                request_body_dict['data'][0]['File name']['type'],
                request_body_dict['data'][0]['Archive size']['value'],
                request_body_dict['data'][0]['Archive size']['type'],
                request_body_dict['data'][0]['Vibro Acceleration RMS']['value'],
                request_body_dict['data'][0]['Vibro Acceleration RMS']['type'],
                request_body_dict['data'][0]['Tempeature']['value'],
                request_body_dict['data'][0]['Tempeature']['type'],
                request_body_dict['data'][0]['Equipment status']['value'],
                request_body_dict['data'][0]['Equipment status']['type'],
                ]

            float_ptrn = re.compile('^[-+]?[0-9]*[\.|\,]?[0-9]+([eE][-+]?[0-9]+)?$')
            tmpr_str = 'N/A' if re.match(float_ptrn,texts[10]) is None else '{} \'C'.format(texts[10])
            equp_stat_str = 'N/A' if texts[12] == 'N/A' else '{} ({})'.format(texts[12],texts[13])
            rms_str = 'N/A' if re.match(float_ptrn,texts[8]) is None else '{:.2f}'.format(float(texts[8]))
            
            text  = '\n'
            text += 'Record date: {}\n'.format(texts[0])
            text += 'File id: {}\n'.format(texts[2])
            text += 'File name: {}\n'.format(texts[4])
            text += 'Archive size: {}\n'.format(texts[6])
            text += 'Vibro Acceleration RMS: {} {}\n'.format(rms_str,texts[9])
            text += 'Tempeature: {} \n'.format(tmpr_str)
            text += 'Equipment status: {} \n'.format(equp_stat_str)

            print('Json: {}'.format(request_body_dict))
        else:
            request_body_dict = {}
            text = greeting
            print('Json: no json payload found')
        print('Response: {}'.format(greeting))
        
        name = 'Vbot service'
        #url = 'http://{}:{}{}'.format(host, port, endpoint)
        #payload = {'some': 'data'}
        #headers = {'content-type': 'application/json'}
        
        headers = {'Authorization': 'vbot_api_token={}'.format(self.vbot_api_token)}
        params = {
            'text':'{}'.format(requests.utils.quote(text)),
            'contacts':'[{{"type":"telegram","tg_bot_api_token":"{}","chat_id":{}}}]'.\
                format(self.vbot_tg_api_token, self.vbot_tg_chat_id),
            'parse_mode':'html'}
        params_text = '&'.join('{}={}'.format(k, v) for k,v in params.items())
        url = 'http://{}:{}/api/v1/publish?{}'.\
            format(self.vbot_host, self.vbot_port, params_text)
        print('Sending URL: {}'.format(url))
        
        #responce = requests.post(url, data=json.dumps(payload), headers=headers)
        responce = requests.post(url, headers)

        status_verbal = 'OK' if responce.status_code == 200 else 'FAIL'
        status_phrase = '\n{} responce is {}:'.format(name, status_verbal)
                        
        print(status_phrase)
        print(responce.status_code)
        print(responce.text if responce.text else 'No payload in responce')

        
        return web.Response(text=greeting)
        #return web.json_response({'msg': greeting})


if __name__ == '__main__':

    try:
        vcloud_fc = vcloud_fiware_connector()
        
        if vcloud_fc.ping_hosts:
            vcloud_fc.ping_remotes()

        if vcloud_fc.subscribe:
            vcloud_fc.set_subscription()

        if vcloud_fc.server_mode:
            vcloud_fc.start_server()

    except Exception as e:
    
        print(e)
