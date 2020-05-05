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

import os, sys, shutil, gc
import time#, datetime
import argparse
import re
import json
import tarfile, bz2
import math

from vbxlib.logging import print_log, datetime_str
from vbxlib.fiware_requests import *
from vbxlib.network import ping_port
# replace original wave lib for reading extensible file format
import vbxlib.replace_python_lib_wave as wave


class vbox_fiware_connector():

    def __init__(self, cfg_path=None):

        parser = argparse.ArgumentParser(description='Short sample app')

        parser.add_argument('--debug', action="store_true", dest="debug_mode", default=False)
        parser.add_argument('--test', action="store_true", dest="test_mode", default=False)
        parser.add_argument('--server', action="store_true", dest="server_mode", default=False)
        parser.add_argument('--ping', action="store_true", dest="ping_hosts", default=False)
        parser.add_argument('--unsubscribe', action="store_true", dest="unsubscribe", default=False)
        parser.add_argument('--subscribe', action="store_true", dest="subscribe", default=False)
        parser.add_argument('--subscribe2', action="store_true", dest="subscribe2", default=False)
        parser.add_argument('--reg-device', action="store_true", dest="reg_device", default=False)
        parser.add_argument('--send-once', action="store_true", dest="send_once", default=False)
        parser.add_argument('--force-update', action="store_true", dest="force_update", default=False)
        parser.add_argument('--batch-processing', action="store_true", dest="batch_processing", default=False)
        parser.add_argument('-dp', '--data_paths', action="store", dest="data_paths", default=None)
        parser.add_argument('-rh', '--remote-host', action="store", dest="remote_host", default=None)

        self.args, self.unknownArgs = parser.parse_known_args()

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
        self.data_dir = '/storage'
        self.data_ext = ['.wav', '.wav.bz2', '.tar.bz2']
        self.cfg_name = 'vbox_fc_cfg.json'
        self.log_name = 'vbox_fc_log.txt'
        self.meta_name = 'vbox_fc_meta.json'
        self.sensivity_correction = 0.0001 #0.00010486

        is_frozen_msg = 'False' if not getattr(sys, 'frozen', False) else \
                        'True, sys._MEIPASS == {}'.format(sys._MEIPASS)

        print_log('DEBUG: __file__ == {}'.format(__file__))
        print_log('DEBUG: is frozen == {}'.format(is_frozen_msg))
        print_log('DEBUG: os.getcwd() == {}'.format(os.getcwd()))
        print_log('DEBUG: sys.argv == {}'.format(sys.argv))
        print_log('DEBUG: known input args == {}\n'.format(self.args))
        print_log('DEBUG: unknown input args == {}'.format(self.unknownArgs))
        print_log('DEBUG: sys.path == \n{}'.format('\n'.join(sys.path)))
        print_log('DEBUG: os.environ[PATH] == \n{}'.format('\n'.join(os.environ['PATH'].split(';'))))


    def find_remote_host(self):

        remote_host = self.args.remote_host
        host_choices = ['localhost','10.8.0.82']
        print_log('INFO: context-broker remote host is {}'.\
            format(remote_host if remote_host is not None else 'not set'))
        
        if remote_host is not None \
            and ping_port(remote_host, self.cb_port, print_out=True):
            print_log('INFO: context-broker remote host+port ping is OK')
        else:
            if remote_host is not None:
                print_log('WARNING: context-broker remote host+port ping is FAIL')
            for host in host_choices:
                if ping_port(host, self.cb_port, print_out=True):
                    remote_host = host
                    break

            if remote_host is not None:
                print_log('INFO: context-broker host has been auto-selected: {}'.format(remote_host))
            else:
                print_log('ERROR: context-broker host auto-selection failed!')
            
        return remote_host


    def ping_remotes(self):

        print_log('INFO: checking fiware components...\n')

        ping_port(self.db_host, self.db_port)
        ping_port(self.cb_host, self.cb_port)
        ping_port(self.dr_host, self.dr_port)
        ping_port(self.iota_host, self.iota_port0)
        
        fiware_check_database(self.db_host, self.db_port);
        fiware_check_cbroker(self.cb_host, self.cb_port);
        fiware_check_draco(self.dr_host, self.dr_port);
        fiware_check_iotagent(self.iota_host, self.iota_port0);


    def update_data_list(self, meta_path='', data_paths=[]):

            if meta_path != '':
                if os.path.isdir(os.path.dirname(meta_path)):
                    meta_file_path = os.path.abspath(self.meta_name)
                else:
                    meta_file_path = os.path.join(self.root_dir, meta_path)
            else:
                meta_file_path = os.path.join(self.root_dir, self.meta_name)

            print_log('DEBUG: metainfo file selected {}'.format(meta_file_path))
            print_log('DEBUG: data paths selected {}'.format(data_paths))

            with open(meta_file_path, 'a+', encoding='utf-8') as meta_file_obj:

                META_UPDATED = False
                if os.stat(meta_file_path).st_size == 0 \
                        or self.args.force_update:
                    metainfo = []
                    self.args.force_update = False
                else:
                    meta_file_obj.seek(0, 0)
                    metainfo = json.load(meta_file_obj)

                existing_files = []

                for d_path in data_paths:
                    if os.path.isdir(d_path):
                        dir_files = [os.path.join(d_path, file) for file in os.listdir(d_path)]
                        existing_files.extend(dir_files)
                    elif os.path.isfile(d_path):
                        existing_files.append(os.path.abspath(d_path))

                print_log('DEBUG: existing files selected: \n{}'.format('\n'.join(existing_files)))

                for data_file_path in existing_files:

                    if data_file_path.endswith('.tar.bz2') \
                        or data_file_path.endswith('.wav.bz2'):

                        data_file_name = os.path.basename(data_file_path)

                        if not any(data_file_name in rec['file_name'] for rec in metainfo):

                            metainfo.append({
                                'file_name': 'N/A',
                                'file_path': data_file_path,
                                'file_ext': 'N/A',
                                'file_date': 'N/A',
                                'file_size': 'N/A',
                                'data_sent': 'N/A',
                                'meta_generated': False,
                                'meta_published': False,
                                'data_processed': False,
                                'vbot_published': False,
                                'file_id': 'N/A',
                                'file_url': None,
                                'point_report_url': None,
                                'equipment_report_url': None,
                                'data_rms': 'N/A',
                                'data_temperature': 'N/A',
                                'data_status':'N/A',
                                'preliminary_status':'N/A',
                                'point_status':'N/A',
                                'equipment_status':'N/A',
                            })
                            META_UPDATED = True

                if META_UPDATED:
                    meta_file_obj.seek(0, 0)
                    json.dump(metainfo, meta_file_obj, ensure_ascii=False, indent=2, sort_keys=True)

                return metainfo


    def update_metainfo(self, metainfo):

        META_UPDATED = False
        for i_rec, rec in enumerate(metainfo):
            if not rec['meta_generated']:
                print_log('DEBUG: generating meta for file {}'.format(rec['file_path']))

                data_file_path = rec['file_path']
                data_file_name = os.path.basename(data_file_path)

                # get file meat from cfg
                if data_file_path.endswith('.tar.bz2'):
                    cfg_file_path = data_file_path.replace('.tar.bz2','.cfg')
                elif data_file_path.endswith('.wav.bz2'):
                    cfg_file_path = data_file_path + '.cfg'
                else:
                    cfg_file_path = ''
                if os.path.isfile(cfg_file_path):
                    with open(cfg_file_path, 'r') as f_obj:
                        text = f_obj.read()
                        package = re.findall('package = (.*)',text)
                        package = package[0] if package else data_file_name
                        sent = re.findall('sent = (.*)',text)
                        sent = sent[0] if sent else 'no'
                        sensor_temp = re.findall('sensor_temp = (.*)',text)
                        sensor_temp = sensor_temp[0] if sensor_temp else 'N/A'
                        wav_start_timestamp = re.findall('wav_start_timestamp = (.*)',text)
                        if wav_start_timestamp:
                            wav_start_timestamp = wav_start_timestamp[0] 
                            wav_start_datetime = datetime_str(wav_start_timestamp)
                        else:
                            wav_start_datetime = None
                        file_id = re.findall('file_id = (.*)',text)
                        file_id = file_id[0] if file_id else None
                        rawdata = re.findall('rawdata = (.*)',text)
                        rawdata = rawdata[0] if rawdata else None
                else:
                    print_log('WARNING: Config file for data {} was not found! Metainfo will not be full.'.format(data_file_path))
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
                try:
                    if os.path.isdir(temp_dir_path):
                        shutil.rmtree(temp_dir_path)
                
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
                        print_log('ERROR: unknown raw data archive type!')


                    # calculate rms
                    t_start = time.time()
                    with wave.open(wav_file_path, 'rb') as waveFile:
                        # e.g. Signed 32 bit Little Endian, Rate 96000 Hz, Stereo
                        waveBytes = waveFile.readframes(waveFile.getnframes())
                        sample_width = waveFile.getsampwidth()
                        frames_number = waveFile.getnframes()
                        print_log('Wav {} has {} channels'.format(wav_file_path, waveFile.getnchannels()))
                        accum = 0
                        for i_frame in range(frames_number):
                            sample_int = int.from_bytes(
                                waveBytes[i_frame * sample_width + 0:i_frame * sample_width + 3],
                                byteorder='little', signed=True)
                            accum += sample_int ** 2
                        rms_value = math.sqrt(accum/frames_number) * self.sensivity_correction
                    print_log('RMS calculation finished in {} sec'.format(time.time()-t_start))
                except Exception as e:
                    print_log('ERROR: file processig failed! {}'.format(e))
                    rms_value = 'N/A'
                
                shutil.rmtree(temp_dir_path)
                gc.collect()

                metainfo[i_rec] = {
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
                }
                META_UPDATED = True
                if not self.args.batch_processing:
                    break

        if META_UPDATED:
            meta_file_path = os.path.join(self.root_dir, self.meta_name)
            with open(meta_file_path, 'w', encoding='utf-8') as meta_file_obj:
                meta_file_obj.seek(0, 0)
                json.dump(metainfo, meta_file_obj, ensure_ascii=False, indent=2, sort_keys=True)

        return metainfo


    def send_metainfo(self, metainfo):

        META_UPDATED = False
        for i_rec, rec in enumerate(metainfo):
            if not rec['meta_published']:
                print_log('DEBUG: sending meta for file {}'.format(rec['file_path']))
                status_1, text = fiware_set_context(self.iota_host, self.iota_port1, 'sensor03', rec)
                status_2, text = fiware_get_context(self.cb_host, self.cb_port)
                if status_1 == 'OK' and status_1 == 'OK':
                    metainfo[i_rec]['meta_published'] = True
                    META_UPDATED = True
                    if not self.args.batch_processing:
                        break
                time.sleep(1) # avoid too frequent updates - cause missing some of them

        if META_UPDATED:
            meta_file_path = os.path.join(self.root_dir, self.meta_name)
            with open(meta_file_path, 'w', encoding='utf-8') as meta_file_obj:
                meta_file_obj.seek(0, 0)
                json.dump(metainfo, meta_file_obj, ensure_ascii=False, indent=2, sort_keys=True)

        return META_UPDATED

    def data_paths_are_in_start_args(self):
        return any(arg.endswith(ext) or os.path.isdir(arg)
                   for arg in sys.argv
                   for ext in self.data_ext)

    def process_metainfo(self, meta_path='', data_paths=[]):

        if meta_path == '':
            meta_path = self.meta_name

        if self.args.test_mode:
            fiware_set_context(self.iota_host, self.iota_port1)
            fiware_get_context(self.cb_host, self.cb_port)
            gc.collect()
            return

        elif data_paths != []:
            metainfo = self.update_data_list(meta_path, data_paths)

        elif self.data_paths_are_in_start_args():
            metainfo = self.update_data_list(meta_path, data_paths=sys.argv)

        elif os.path.isdir(self.data_dir):
            metainfo = self.update_data_list(meta_path, data_paths=[self.data_dir])

        else:
            metainfo = self.update_data_list(meta_path, data_paths=[self.root_dir])

        metainfo = self.update_metainfo(metainfo)

        META_UPDATED = self.send_metainfo(metainfo)

        gc.collect()


    def start_server(self):

        while True:

            if self.args.data_paths is not None \
                    and os.path.exists(self.args.data_paths):
                metainfo = self.update_data_list(data_paths=[self.args.data_paths])

            elif self.data_paths_are_in_start_args():
                metainfo = self.update_data_list(data_paths=sys.argv)

            else:
                metainfo = self.update_data_list(data_paths=[self.root_dir])
            
            metainfo = self.update_metainfo(metainfo)

            META_UPDATED = self.send_metainfo(metainfo)

            if META_UPDATED:
                gc.collect()
            else:
                # check local storage for new data files once per minute
                time.sleep(60)


        
if __name__ == '__main__':

    try:
    
        vbox_fc = vbox_fiware_connector()
        
        if vbox_fc.args.ping_hosts:
            vbox_fc.ping_remotes()
            
        if vbox_fc.args.unsubscribe:
            fiware_rem_subscriptions(vbox_fc.cb_host, vbox_fc.cb_port) 
            
        if vbox_fc.args.subscribe:
            fiware_set_subscription_for_draco(vbox_fc.cb_host, vbox_fc.cb_port)
            fiware_get_subscriptions(vbox_fc.cb_host, vbox_fc.cb_port)
            
        if vbox_fc.args.subscribe2:
            fiware_set_subscription_for_vcloud_fc(vbox_fc.cb_host, vbox_fc.cb_port)
            fiware_get_subscriptions(vbox_fc.cb_host, vbox_fc.cb_port)

        if vbox_fc.args.reg_device:
            fiware_set_device(vbox_fc.iota_host, vbox_fc.iota_port0)
            fiware_set_service(vbox_fc.iota_host, vbox_fc.iota_port0)

        if vbox_fc.args.send_once:
            vbox_fc.process_metainfo()

        if vbox_fc.args.server_mode:
            vbox_fc.start_server()

    except KeyboardInterrupt:
        # someone pressed ctr+c
        print_log('Keyboard Interrupt (Ctrl+C)')

    except Exception as e:
        # unknown exception
        print_log('ERROR: {}\nDEBUG:\n'.format(e))
        import sys, traceback
        print(traceback.print_exc(file=sys.stdout))
