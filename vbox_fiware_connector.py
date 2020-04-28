# vbox_fiware_connector
# v1.0, 2020-04-26, RTG, Vibrobox

"""
Способы работы:

1. при одиночном вызыове скрипта - проверяется подключение и статус фивара
2. при вызове с параметром файл - обработка и отправка файла
3. при вызове с параметром --server - запускается фоновый сервер, 
который сам чекает и отправляет файлы (выполняет п.1 и п.2)
4. при импорте как библиотека - предоставляет свои функции

прием команд извне возможен (для режима --server), но не разрабатывается

Архитектура:

Класс vbox_fiware_connector

Инициализируется настройками 
подключения к фивару, поиска и обработки файлов, заполнения метаинфы
все необх. настройки заданы по дефолту, но можно прокинуть файлом конфига (json).
в процессе работы пишет в консоль и в лог-файл (txt).
в отдельном файле хранит список и метаинф найденных/обработанных/переданных файлов.

Методы класса

инит
загрузка конфига
настрока логгера
обновить сисок фалов и метаинфы
проверить подключнеие
тест - сисок фиктивный список фалов и метаинфы
посчитать мету для файла (сложность опциональна)
тест - сгенерировать фиктивную мету для файла
зарегистрировать новый мету по файлу
отправить мету по файлу

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

import os, sys
from vbxlib.fiware_requests import *
from vbxlib.network import ping_port as ping_port

class vbox_fiware_connector():

    def __init__(self, cfg_path=None):

        self.db_host = 'localhost' # common host, MONGODB_HOST env variable
        self.db_port = '27017' # mongo database, MONGODB_PORT env variable
        self.cb_host = 'localhost' # common host, CONTEXT_BROKER_HOST env variable
        self.cb_port = '1026' # common host, CONTEXT_BROKER_PORT env variable
        self.dr_host = 'localhost' # common host, DRACO_HOST env variable
        self.dr_port = '9090' # draco (preserves history), DRACO_PORT0 env variable
        self.iota_host = 'localhost' # common host, IOT_AGENT_HOST env variable
        self.iota_port0 = '4041' # iot-agent (mqtt+json to ngsi converter), IOT_AGENT_PORT0 env variable
        self.iota_port1 = '7896' # iot-agent (mqtt+json to ngsi converter), IOT_AGENT_PORT1 env variable

        self.root_dir = '.'
        self.data_dir = '.'
        self.data_types = ['.wav', '.wav.bz2', '.tar.bz2']
        self.cfg_name = 'vbox_fc_cfg.json'
        self.log_name = 'vbox_fc_log.txt'
        self.meta_name = 'vbox_fc_meta.json'

        def wavs_are_in_start_args():
            print('DEBUG: sys.argv == {}'.format(sys.argv))
            return any(arg.endswith(ext) 
                       for arg in sys.argv 
                       for ext in self.data_types)

        self.test_mode = True or '--test' in sys.argv
        self.debug_mode = True or '--debug' in sys.argv
        self.ping_hosts = False or '--ping' in sys.argv
        self.subscribe = False or  '--subscribe' in sys.argv
        self.subscribe2 = False or  '--subscribe2' in sys.argv
        self.send_once = False or '--send_once' in sys.argv or wavs_are_in_start_args() 
        self.server_mode = False or '--server' in sys.argv

    
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
    
        fiware_set_subscription(self.cb_host, self.cb_port);
        fiware_get_subscription(self.cb_host, self.cb_port);


    def set_subscription2(self):
    
        fiware_set_subscription2(self.cb_host, self.cb_port);
        fiware_get_subscription(self.cb_host, self.cb_port);


    def set_device(self):
    
        fiware_set_device(self.iota_host, self.iota_port0);
        fiware_set_service(self.iota_host, self.iota_port0);


    def send_meta(self):
    
        fiware_set_context(self.iota_host, self.iota_port1);
        fiware_get_context(self.cb_host, self.cb_port);


if __name__ == '__main__':

    try:
    
        vbox_fc = vbox_fiware_connector()
        
        if vbox_fc.ping_hosts:
            vbox_fc.ping_remotes()
            
        if vbox_fc.subscribe:
            vbox_fc.set_subscription()
            vbox_fc.set_device()
            
        if vbox_fc.subscribe2:
            vbox_fc.set_subscription2()

        if vbox_fc.send_once:
            vbox_fc.send_meta()

        if vbox_fc.server_mode:
            vbox_fc.start_server()

    except Exception as e:
    
        print(e)
