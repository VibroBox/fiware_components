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
import json
from vbxlib.fiware_requests import *
from vbxlib.network import ping_port as ping_port

# Import replaced wav lib for reading extensible format
#import Lib.wave as wave
import wave
import tarfile, bz2
import re
import shutil
import math
import gc
import time, datetime

class vbox_fiware_connector():

    def __init__(self, cfg_path=None):

        self.cb_port = '1026' # common host, CONTEXT_BROKER_PORT env variable
        self.cb_host = self.find_remote_host() # common host, CONTEXT_BROKER_HOST env variable
        self.db_host = self.cb_host # common host, MONGODB_HOST env variable
        self.db_port = '27017' # mongo database, MONGODB_PORT env variable
        self.dr_host = self.cb_host # common host, DRACO_HOST env variable
        self.dr_port = '9090' # draco (preserves history), DRACO_PORT0 env variable
        self.iota_host = self.cb_host # common host, IOT_AGENT_HOST env variable
        self.iota_port0 = '4041' # iot-agent (mqtt+json to ngsi converter), IOT_AGENT_PORT0 env variable
        self.iota_port1 = '7896' # iot-agent (mqtt+json to ngsi converter), IOT_AGENT_PORT1 env variable

        self.root_dir = '.'
        #self.data_dir = '/storage'
        self.data_dir = '.'
        self.data_ext = ['.wav', '.wav.bz2', '.tar.bz2']
        self.cfg_name = 'vbox_fc_cfg.json'
        self.log_name = 'vbox_fc_log.txt'
        self.meta_name = 'vbox_fc_meta.json'
        self.sensivity_correction = 0.0001 #0.00010486

        print('DEBUG: sys.argv == {}'.format(sys.argv))
        self.test_mode = False or '--test' in sys.argv
        self.debug_mode = True or '--debug' in sys.argv
        self.ping_hosts = False or '--ping' in sys.argv
        self.unsubscribe = False or  '--unsubscribe' in sys.argv
        self.subscribe = False or  '--subscribe' in sys.argv
        self.subscribe2 = False or  '--subscribe2' in sys.argv
        self.reg_device = False or  '--reg-device' in sys.argv
        self.send_once = False or '--send-once' in sys.argv
        self.force_update = False or '--force-update' in sys.argv
        self.server_mode = False or '--server' in sys.argv

    
    def find_remote_host(self):

        remote_host = None
        host_choices = ['10.8.0.82','localhost']

        for host in host_choices:
            #if ping_port(host, self.cb_port, print_out=False):
            if ping_port(host, self.cb_port, print_out=True):
                remote_host = host
                break

        if remote_host is not None:
            print('INFO: context-broker host has been auto-selected: {}'.format(remote_host))
        else:
            print('ERROR: context-broker host auto-selection failed!')
            remote_host = host_choices[0] # DEBUG TEST
            
        return remote_host


    def ping_remotes(self):

        print('\nINFO: checking fiware components...\n')

        print(ping_port(self.db_host, self.db_port))
        ping_port(self.cb_host, self.cb_port)
        ping_port(self.dr_host, self.dr_port)
        ping_port(self.iota_host, self.iota_port0)
        
        fiware_check_database(self.db_host, self.db_port);
        fiware_check_cbroker(self.cb_host, self.cb_port);
        fiware_check_draco(self.dr_host, self.dr_port);
        fiware_check_iotagent(self.iota_host, self.iota_port0);


    def update_metainfo(self, meta_path='', data_paths=[]):

            if meta_path != '':
                if os.path.isdir(os.path.dirname(meta_path)):
                    meta_file_path = os.path.abspath(self.meta_name)
                else:
                    meta_file_path = os.path.join(self.root_dir, meta_path)
            else:
                meta_file_path = os.path.join(self.root_dir, self.meta_name)

            with open(meta_file_path, 'a+', encoding='utf-8') as meta_file_obj:

                META_UPDATED = False
                if os.stat(meta_file_path).st_size > 0:
                    meta_file_obj.seek(0, 0)
                    metainfo = json.load(meta_file_obj)
                else:
                    metainfo = []

                existing_files = []
                print(data_paths)
                for d_path in data_paths:
                    if os.path.isdir(d_path):
                        dir_files = [os.path.join(d_path, file) for file in os.listdir(d_path)]
                        existing_files.extend(dir_files)
                    elif os.path.isfile(d_path):
                        existing_files.append(os.path.abspath(d_path))

                for data_file_path in existing_files:

                    if '.tar.bz2' in data_file_path or '.wav.bz2' in data_file_path:

                        data_file_name = os.path.basename(data_file_path)

                        if not any(data_file_name in rec['file_name'] for rec in metainfo) \
                                or self.force_update:

                            # get file meat from cfg
                            if '.tar.bz2' in data_file_path:
                                cfg_file_path = data_file_path.replace('.tar.bz2','.cfg')
                            elif '.wav.bz2' in data_file_path:
                                cfg_file_path = data_file_path.replace('.wav.bz2', '.cfg')
                            else:
                                cfg_file_path = ''
                            if os.path.isfile(cfg_file_path):
                                with open(cfg_file_path, 'r') as f_obj:
                                    text = f_obj.read()
                                    package = re.findall('package = (.*)',text)[0]
                                    sent = re.findall('sent = (.*)',text)[0]
                                    sensor_temp = re.findall('sensor_temp = (.*)',text)[0]
                                    wav_start_timestamp = re.findall('wav_start_timestamp = (.*)',text)[0]
                                    file_id = re.findall('file_id = (.*)',text)[0]
                                    rawdata = re.findall('rawdata = (.*)',text)[0]
                                wav_start_datetime = datetime.datetime.fromtimestamp(float(wav_start_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                print('WARNING: Config file for data {} was not found! Metainfo will not be full.'.format(data_file_path))
                                package = data_file_name # archive name
                                sent = 'no' # it is supposed that the file hasn't been sent yet
                                sensor_temp = 'N/A' # temperature
                                wav_start_timestamp = None # time of wav record start
                                file_id = None # id in our database, according to sending order
                                rawdata = None # wav file name
                                wav_start_datetime = None

                            # get archive size
                            def mb_size(size):
                                # Developer: Ratgor
                                # Date: 28.07.2019 (??? 2020-05-01)
                                # Version: v1.0
                                size_suffix = ['B', 'kB', 'MB', 'GB', 'TB']
                                power_level = 0
                                while (size / 1024 > 0.5):
                                    size = size / 1024
                                    power_level += 1
                                if not power_level:
                                    return '{} B'.format(size)
                                elif size < 10:
                                    return '{:.2f} {}'.format(size, size_suffix[power_level])
                                else:
                                    return '{:.1f} {}'.format(size, size_suffix[power_level])

                            archive_size = mb_size(os.stat(data_file_path).st_size)

                            # extract data
                            temp_dir_path = data_file_path.lower().replace('.bz2', '_temp')
                            # Vbox RPi platform (due to write permissions)
                            if 'uname' in dir(os) and 'raspberrypi' in os.uname():
                                temp_dir_path = os.path.join(os.getcwd(), os.path.basename(temp_dir_path))
                            if '.tar.bz2' in data_file_path:
                                with tarfile.open(data_file_path, 'r:*') as tar:
                                    tar.extractall(temp_dir_path)
                                temp_files_path = [os.path.join(r, f) for r, dd, ff in os.walk(temp_dir_path) for f in ff]
                                if rawdata is not None:
                                    wav_file_path = [f_path for f_path in temp_files_path if rawdata in f_path][0]
                                else:
                                    wav_file_path = [f_path for f_path in temp_files_path if '.wav' in f_path][0]
                            elif '.wav.bz2' in data_file_path:
                                if not os.path.isdir(temp_dir_path):
                                    os.makedirs(temp_dir_path)
                                wav_file_path = os.path.join(temp_dir_path, os.path.basename(
                                    data_file_path.lower().replace('.wav.bz2', '.wav')))
                                with open(data_file_path, 'rb') as source, \
                                        open(wav_file_path, 'wb') as dest:
                                    dest.write(bz2.decompress(source.read()))
                            else:
                                print('ERROR: unknown raw data archive type!')


                            # calculate rms
                            t_start = time.time()
                            with wave.open(wav_file_path, 'rb') as waveFile:
                                waveBytes = waveFile.readframes(waveFile.getnframes())
                                sample_width = waveFile.getsampwidth()
                                frames_number = waveFile.getnframes()
                                print('Wav {} has {} channels'.format(wav_file_path, waveFile.getnchannels()))
                                accum = 0
                                for i_frame in range(frames_number):
                                    sample_int = int.from_bytes(
                                        waveBytes[i_frame * sample_width + 0:i_frame * sample_width + 3],
                                        byteorder='little', signed=True)
                                    accum += sample_int ** 2
                                rms_value = math.sqrt(accum/frames_number) * self.sensivity_correction
                            print('RMS calculation finished in {} sec'.format(time.time()-t_start))

                            shutil.rmtree(temp_dir_path)
                            gc.collect()

                            metainfo.append({
                                'file_name': package,
                                'file_path': data_file_path,
                                'file_ext': '.tar.bz2',
                                'file_date': wav_start_datetime,
                                'file_size': archive_size,
                                'data_sent': sent == 'yes',
                                'meta_generated': True,
                                'meta_published': False,
                                'data_processed': False,
                                'vbot_published': False,
                                'file_id': file_id,
                                'file_url': None,
                                'point_report_url': None,
                                'equipment_report_url': None,
                                'data_rms': rms_value,
                                'data_temperature': sensor_temp,
                                'data_status':'N/A',
                                'preliminary_status':'N/A',
                                'point_status':'N/A',
                                'equipment_status':'N/A',
                            })
                            META_UPDATED = True

                if META_UPDATED:
                    meta_file_obj.seek(0, 0)
                    json.dump(metainfo, meta_file_obj, ensure_ascii=False, indent=2, sort_keys=True)
                else:
                    print('INFO: no new matainfo published')

                return metainfo


    def send_metainfo(self, metainfo):

        META_UPDATED = False
        for i_rec, rec in enumerate(metainfo):
            if not rec['meta_published']:
                fiware_set_context(self.iota_host, self.iota_port1, 'sensor03', rec)
                fiware_get_context(self.cb_host, self.cb_port)
                metainfo[i_rec]['meta_published'] = True
                META_UPDATED = True
                time.sleep(1) # avoid too frequent updates - cause missing some of them

        if META_UPDATED:
            meta_file_path = os.path.join(self.root_dir, self.meta_name)
            with open(meta_file_path, 'w', encoding='utf-8') as meta_file_obj:
                meta_file_obj.seek(0, 0)
                json.dump(metainfo, meta_file_obj, ensure_ascii=False, indent=2, sort_keys=True)

        return metainfo

    def data_is_in_start_args(self):
        return any(arg.endswith(ext) or (os.path.exists(arg) and not arg.endswith('.py'))
                   for arg in sys.argv
                   for ext in self.data_ext)

    def process_metainfo(self, meta_path='', data_paths=[]):

        if meta_path == '':
            meta_path = self.meta_name

        if self.test_mode:
            fiware_set_context(self.iota_host, self.iota_port1)
            fiware_get_context(self.cb_host, self.cb_port)
            return

        elif data_paths != []:
            metainfo = self.update_metainfo(meta_path, data_paths)

        elif self.data_is_in_start_args():
            metainfo = self.update_metainfo(meta_path, data_paths=sys.argv)

        elif os.path.isdir(self.data_dir):
            metainfo = self.update_metainfo(meta_path, data_paths=[self.data_dir])

        else:
            metainfo = self.update_metainfo(meta_path, data_paths=[self.root_dir])

        metainfo = self.send_metainfo(metainfo)


    def start_server(self):

        while True:

            if self.data_is_in_start_args():
                metainfo = self.update_metainfo(data_paths=sys.argv)

            elif os.path.isdir(self.data_dir):
                metainfo = self.update_metainfo(data_paths=[self.data_dir])

            else:
                metainfo = self.update_metainfo(data_paths=[self.root_dir])

            metainfo = self.send_metainfo(metainfo)

            # check local storage for new data files once per minute
            time.sleep(60)


        
if __name__ == '__main__':

    try:
    
        vbox_fc = vbox_fiware_connector()
        
        if vbox_fc.ping_hosts:
            vbox_fc.ping_remotes()
            
        if vbox_fc.unsubscribe:
            fiware_rem_subscriptions(vbox_fc.cb_host, vbox_fc.cb_port) 
            
        if vbox_fc.subscribe:
            fiware_set_subscription_for_draco(vbox_fc.cb_host, vbox_fc.cb_port)
            fiware_get_subscriptions(vbox_fc.cb_host, vbox_fc.cb_port)
            
        if vbox_fc.subscribe2:
            fiware_set_subscription_for_vcloud_fc(vbox_fc.cb_host, vbox_fc.cb_port)
            fiware_get_subscriptions(vbox_fc.cb_host, vbox_fc.cb_port)

        if vbox_fc.reg_device:
            fiware_set_device(vbox_fc.iota_host, vbox_fc.iota_port0)
            fiware_set_service(vbox_fc.iota_host, vbox_fc.iota_port0)

        if vbox_fc.send_once:
            vbox_fc.process_metainfo()

        if vbox_fc.server_mode:
            vbox_fc.start_server()

    except KeyboardInterrupt:
        # someone pressed ctr+c
        print('Keyboard Interrupt (Ctrl+C)')

    except Exception as e:
        # unknown exception
        print('ERROR: {}\nDEBUG:\n'.format(e))
        import sys, traceback
        print(traceback.print_exc(file=sys.stdout))
