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

def fiware_ping_service(name, host, port, endpoint='', ok_code=200):

    url = 'http://{}:{}{}'.format(host, port, endpoint)
    responce = requests.get(url)
    
    status_verbal = 'OK' if responce.status_code == ok_code else 'FAIL'
    status_phrase = '\n{} responce is {}:'.format(name, status_verbal)
                    
    print(status_phrase)
    print(responce.status_code)
    print(responce.text)    

   
def fiware_check_database(host, port):
    fiware_ping_service('Mongo DB', host, port, endpoint='')  

   
def fiware_check_cbroker(host, port):
    fiware_ping_service('Orion Context Broker', host, port, '/version')  
   
    
def fiware_check_draco(host, port):
    fiware_ping_service('Draco', host, port, '/nifi-api/system-diagnostics')  

   
def fiware_check_iotagent(host, port):
    fiware_ping_service('IoT Agent', host, port, '/iot/about')  


def fiware_send_request(name, reqtype, host, port, endpoint, headers, payload, ok_code):

    url = 'http://{}:{}{}'.format(host, port, endpoint)
    #url = 'https://api.github.com/some/endpoint'
    #payload = {'some': 'data'}
    #headers = {'content-type': 'application/json'}

    if reqtype == 'GET':
        responce = requests.get(url, headers=headers)
        
    elif reqtype == 'POST':
        responce = requests.post(url, data=json.dumps(payload), headers=headers)

    status_verbal = 'OK' if responce.status_code == ok_code else 'FAIL'
    status_phrase = '\n{} responce is {}:'.format(name, status_verbal)
                    
    print(status_phrase)
    print(responce.status_code)
    print(responce.text if responce.text else 'No payload in responce')    
   
   
def fiware_set_subscription(host, port):
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
              "url": "http://localhost:5050/v2/notify"
            }
          },
          "throttling": 1
        }
    ok_code=201
    fiware_send_request(name, 'POST', host, port, endpoint, headers, payload, ok_code)


def fiware_get_subscription(host, port):
    name='get subscription'
    endpoint='/v2/subscriptions'
    headers = {'accept': 'application/json',
               'fiware-service': 'vibrobox',
               'fiware-servicepath': '/'}
    payload = {}
    ok_code=200
    fiware_send_request(name, 'GET', host, port, endpoint, headers, payload, ok_code)


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
                          { "object_id": "rms", "name": "Vibro Acceleration RMS", "type": "mm/s^2" },
                          { "object_id": "size", "name": "Archive size", "type": "Mbytes" },
                          { "object_id": "status", "name": "Equipment status", "type": "subjective estimation" },
                          { "object_id": "tree", "name": "metainfo tree test", "type": "test nested metainfo" }
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


def fiware_set_context(host, port):
    name='set context'
    endpoint='/iot/json?k=ANYKEY&i=sensor03'
    headers = {'content-type': 'application/json'}
    payload = \
        {
            "rms": 78,
            "size": "12.4",
            "status": "Not bad",
            "tree": 
                {
                    "really?":"true"
                }
        }
    ok_code=200
    fiware_send_request(name, 'POST', host, port, endpoint, headers, payload, ok_code)


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
    fiware_send_request(name, 'POST', host, port, endpoint, headers, payload, ok_code)
