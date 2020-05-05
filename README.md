# fiware_components
reference components for vibrobox-fiware integration

# deploy & run vcloud-fc

open root dir vbx_fiware_comps
(root of the project = git repo root dir)

git clone https://github.com/VibroBox/fiware_components/
git checkout development

put .env file (or rename and edit .env.prod) to the vbx_fiware_comps dir

extract the vibrobox_bot (vbot) archive

set the path to the vbot dir it the .env file

start docker-compose.yml by running from root dir:
docker-compose stop # if smth is running
docker-compose rm # y+Enter to reset containers
docker-compose up -d # start all in backgroud
docker-compose build vcloud-fc # rebuild example

check no errors with commands:
docker-compose ps #all services should be "UP" and docker-compose logs 
docker-compose logs vbot
docker-compose logs vcloud-fc
docker-compose logs | grep "something"

open draco web interface 
http://localhost:9090/nifi/

add three-component template for "orion-to-mongo"

set url in  draco component "NGSItoMongo -> view configuration -> properties -> Mongo URI"
mongodb://localhost:27017

run all draco components by "play" triangle icon

call with python: 

./python382x86/python.exe ./vbox_fiware_connector.py --ping

./python382x86/python.exe ./vbox_fiware_connector.py --unsubscribe --subscribe --subscribe2

./python382x86/python.exe ./vbox_fiware_connector.py --reg-device

./python382x86/python.exe ./vbox_fiware_connector.py --send-once --test

./python382x86/python.exe ./vbox_fiware_connector.py --send_once


## compile & run vbox-fc
  
1. open git bash in `H:\Work\Git\vbx_fiware_comps`
  
2. run `docker-compose -f ./docker-compose-build-vbox-fc.yml build vbox-fc-build && docker-compose -f ./docker-compose-build-vbox-fc.yml up`
  
3. prepare target dir at a vbox device, e.g. `mkdir ./fiware/ && chmod -R 777 ./fiware/`
  
5. copy executable `vbox_fiware_connector` to target vbox dir, e.g. `/home/pi/fiware` and set execute permissions
  
6. cd to the dir (like `cd ./fiware`) and run the executable from vbox console like `./vbox_fiware_connector --server`,  
  
or run-once with logs:
```
./vbox_fiware_connector --send-once -dp "/storage/271.2.tar.bz2" -rh 10.8.0.82 --force-update > ./vbox_fc_log.txt 2>&1 & echo $! > vbox_fc_pid.txt
```
  
or start in background (second line of the example - to check, third line - stop):  
```
nohup ./vbox_fiware_connector --server -dp "/storage" -rh 10.8.0.82 > ./vbox_fc_log.txt 2>&1 & echo $! > vbox_fc_pid.txt
ps
kill -9 `cat vbox_fc_pid.txt` && rm vbox_fc_pid.txt 
```


## 5. opent ports  

5.1 windows 10  

5.1.1 run `firewall.cpl`  

5.1.2 add incoming rule `all local ports` for `ICMPv4` (for pinging vcloud-fc)  

5.1.2 add incoming rule loacal `7797, 1026, 7896, 4041` or `1026, 4041, 7896, 7797, 8089, 8443, 5050, 9090, 27017` for TCP (for incoming vcloud-fc)  

5.1.3 (reset win 10 firewall and pc restart had been required before creating firewall rules during testing)  

5.1.4 check the ports are opened, e.g. `netstat -a | grep LISTEN`, `netstat -a -n -o | grep LISTEN`  

5.1.5 check the hots is pinging from vbox, e.g. `ping 10.8.0.82`, `nmap 10.8.0.82 -Pn`, `nc -vz 10.8.0.82 1026`  


