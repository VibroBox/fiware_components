# fiware_requests
# v1.0, 2020-04-26, RTG, Vibrobox

"""
Методы запросов к фивару (отдельная либа fiware_requests)

пингануть сервер
проверить базу данных
проверить контекст брокер
проверить иот агент
проверить драко
отправить запрос - зарегистрировать подписку
отправить запрос - проверить подписку
отправить запрос - зарегать сущность / оборудование
отправить запрос - зарегать сервис / категорию оборудования
отправить запрос - записать мету
отправить запрос - прочитать мету
отправить запрос - удалить геристрацию мету

"""
import requests, json
from vbxlib.logging import print_log, datetime_str

def fiware_ping_service(name, host, port, endpoint='', ok_code=200):
    try:
        url = 'http://{}:{}{}'.format(host, port, endpoint)
        responce = requests.get(url)
        
        status_verbal = 'OK' if responce.status_code == ok_code else 'FAIL'
        status_phrase = '\n{} responce is {}:'.format(name, status_verbal)
        responce_text = (responce.text if responce.text else 'No text in responce')
                        
        print(status_phrase)
        print(responce.status_code)
        print(responce_text)    
    except Exception as e:
        # unknown exception
        print_log('ERROR: {}\nDEBUG:\n'.format(e))
        import sys, traceback
        print(traceback.print_exc(file=sys.stdout))
        status_verbal = 'FAIL'
        responce_text = 'ERROR: {}'.format(e)
        
    return status_verbal, responce_text
   
def fiware_check_database(host, port):
    fiware_ping_service('Mongo DB', host, port, endpoint='')  

   
def fiware_check_cbroker(host, port):
    fiware_ping_service('Orion Context Broker', host, port, '/version')  
   
    
def fiware_check_draco(host, port):
    fiware_ping_service('Draco', host, port, '/nifi-api/system-diagnostics')  

   
def fiware_check_iotagent(host, port):
    fiware_ping_service('IoT Agent', host, port, '/iot/about')  


def fiware_send_request(name, reqtype, host, port, endpoint, headers, payload, ok_code):
    try:
        url = 'http://{}:{}{}'.format(host, port, endpoint)
        #url = 'https://api.github.com/some/endpoint'
        #payload = {'some': 'data'}
        #headers = {'content-type': 'application/json'}

        if reqtype == 'GET':
            responce = requests.get(url, headers=headers)
            
        elif reqtype == 'POST':
            responce = requests.post(url, data=json.dumps(payload), headers=headers)

        elif reqtype == 'DELETE':
            responce = requests.delete(url, headers=headers)

        status_verbal = 'OK' if responce.status_code == ok_code else 'FAIL'
        status_phrase = '\n{} responce is {}:'.format(name, status_verbal)
        responce_text = (responce.text if responce.text else 'No text in responce')
                        
        print(status_phrase)
        print(responce.status_code)
        print(responce_text)    
    except Exception as e:
        # unknown exception
        print_log('ERROR: {}\nDEBUG:\n'.format(e))
        import sys, traceback
        print(traceback.print_exc(file=sys.stdout))
        status_verbal = 'FAIL'
        responce_text = 'ERROR: {}'.format(e)
        
    return status_verbal, responce_text
   
   
def fiware_set_subscription_for_draco(host, port):
    name='set subscription'
    endpoint='/v2/subscriptions'
    headers = {'content-type': 'application/json',
               'fiware-service': 'vibrobox',
               'fiware-servicepath': '/'}
    payload = \
        {
          "description": "Notify Draco of all context changes",
          "subject": {
            "entities": [
              {
                "idPattern": ".*"
              }
            ]
          },
          "notification": {
            "http": {
              "url": "http://draco:5050/v2/notify"
            }
          },
          "throttling": 1
        }
    ok_code=201
    fiware_send_request(name, 'POST', host, port, endpoint, headers, payload, ok_code)


def fiware_set_subscription_for_vcloud_fc(host, port):
    name='set subscription'
    endpoint='/v2/subscriptions'
    headers = {'content-type': 'application/json',
               'fiware-service': 'vibrobox',
               'fiware-servicepath': '/'}
    payload = \
        {
          "description": "Notify Vcloud Fiware Connector of all context changes",
          "subject": {
            "entities": [
              {
                "idPattern": ".*"
              }
            ]
          },
          "notification": {
            "http": {
              "url": "http://vcloud-fc:7797/api/v1/notify"
            }
          },
          "throttling": 1
        }
    ok_code=201
    fiware_send_request(name, 'POST', host, port, endpoint, headers, payload, ok_code)


def fiware_get_subscriptions(host, port):
    name='get subscription'
    endpoint='/v2/subscriptions'
    headers = {'accept': 'application/json',
               'fiware-service': 'vibrobox',
               'fiware-servicepath': '/'}
    payload = {}
    ok_code=200
    fiware_send_request(name, 'GET', host, port, endpoint, headers, payload, ok_code)


def fiware_rem_subscriptions(host, port):
    name='rem subscription'
    endpoint='/v2/subscriptions'
    headers = {'accept': 'application/json',
               'fiware-service': 'vibrobox',
               'fiware-servicepath': '/'}
    payload = {}
    ok_code=200
    status, text = fiware_send_request(name, 'GET', host, port, endpoint, headers, payload, ok_code)
    
    subscriptions_dict = json.loads(text)
    for subscription in subscriptions_dict:
        endpoint='/v2/subscriptions/{}'.format(subscription["id"])
        ok_code=204
        status, text = fiware_send_request(name, 'DELETE', host, port, endpoint, headers, payload, ok_code)


def fiware_set_device(host, port):
    name='set device'
    endpoint='/iot/devices'
    headers = {'content-type': 'application/json',
               'fiware-service': 'vibrobox',
               'fiware-servicepath': '/',
               'Cache-Control': 'no-cache'}
    payload = \
        {
            "devices": [
                {
                    "device_id": "sensor03",
                    "entity_name": "customersEquipment",
                    "entity_type": "vibroAccelerationSensor",
                    "attributes": [
                        {"object_id": "file_name", "name": "File name", "type": "string" },
                        {"object_id": "file_path", "name": "File path", "type": "string" },
                        {"object_id": "file_ext", "name": "File extension", "type": "string" },
                        {"object_id": "file_date", "name": "Record time", "type": "timestamp" },
                        {"object_id": "file_size", "name": "Archive size", "type": "Mbytes" },
                        {"object_id": "data_sent", "name": "data_sent", "type": "boolean" },
                        {"object_id": "meta_generated", "name": "meta_generated", "type": "boolean" },
                        {"object_id": "meta_published", "name": "meta_published", "type": "boolean" },
                        {"object_id": "data_processed", "name": "data_processed", "type": "boolean" },
                        {"object_id": "vbot_published", "name": "vbot_published", "type": "boolean" },
                        {"object_id": "file_id", "name": "File id", "type": "numeric" },
                        {"object_id": "file_url", "name": "File url", "type": "url" },
                        {"object_id": "point_report_url", "name": "Point report url", "type": "url2" },
                        {"object_id": "equipment_report_url", "name": "Equipment report url", "type": "url" },
                        {"object_id": "data_rms", "name": "Vibro Acceleration RMS", "type": "mm/s^2" },
                        {"object_id": "data_temperature", "name": "Tempeature", "type": "C" },
                        {"object_id": "data_status", "name": "Data status", "type": "subjective" },
                        {"object_id": "preliminary_status", "name": "Preliminary status", "type": "subjective" },
                        {"object_id": "point_status", "name": "Point status", "type": "subjective" },
                        {"object_id": "equipment_status", "name": "Equipment status", "type": "subjective" }
                    ]
                }
            ]
        }
    ok_code=201
    fiware_send_request(name, 'POST', host, port, endpoint, headers, payload, ok_code)


def fiware_set_service(host, port):
    name='set service'
    endpoint='/iot/services'
    headers = {'content-type': 'application/json',
               'fiware-service': 'vibrobox',
               'fiware-servicepath': '/',
               'Cache-Control': 'no-cache'}
    payload = \
        {
            "services": [
              {
                  "resource": "/iot/json",
                  "apikey": "ANYKEY",
                  "type": "vibroAccelerationSensor"
              }
            ]
        }
    ok_code=201
    fiware_send_request(name, 'POST', host, port, endpoint, headers, payload, ok_code)


def fiware_set_context(host, port, path='sensor03', context={}):
    name='set context'
    endpoint='/iot/json?k={}&i={}'.format('ANYKEY', path)
    headers = {'content-type': 'application/json'}
    payload = context if context != {} else \
        {
            'file_name': 'iFile.iCh.tar.bz2-or-rawdata.wav.bz2',
            'file_path': './.',
            'file_ext': '.tar.bz2',
            'file_date': '2020-05-01 12:00:00',
            'file_size': '12.5 MB',
            'data_sent': False,
            'meta_generated': False,
            'meta_published': False,
            'data_processed': False,
            'vbot_published': False,
            'file_id': 12345,
            'file_url': None,
            'point_report_url': None,
            'equipment_report_url': None,
            'data_rms': 0.0,
            'data_temperature': 'N/A',
            'data_status':'N/A',
            'preliminary_status':'N/A',
            'point_status':'N/A',
            'equipment_status':'N/A',
        }
    ok_code=200
    status, text = fiware_send_request(name, 'POST', host, port, endpoint, headers, payload, ok_code)
    return status, text

def fiware_get_context(host, port):
    name='get context'
    endpoint='/v1/queryContext'
    headers = {'content-type': 'application/json',
               'fiware-service': 'vibrobox',
               'fiware-servicepath': '/',
               'Cache-Control': 'no-cache'}
    payload = \
        {
            "entities": [
                {
                    "isPattern": "false",
                    "id": "customersEquipment",
                    "type": "vibroAccelerationSensor"
                }
            ]
        }
    ok_code=200
    status, text = fiware_send_request(name, 'POST', host, port, endpoint, headers, payload, ok_code)
    return status, text