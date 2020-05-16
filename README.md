#It's highly recommended to set up automatic conversion of endlines for Linux users:
git config --global core.autocrlf=input
#Then Windows users should configue their git in thhis way:
git config --global core.autocrlf=true



# fiware_components
reference components for vibrobox-fiware integration


# dependencies

This manual uses next dependencies  

1. Win10x64 (was tested, any other OS can be used)

2. Git with git bash (was tested, any other unux shell can be used)

3. Docker Desktop for Windows (was tested, any other docker service can be used)

4. Thirdpart docker images: mongo, fiware/orion, fiware/iotagent-json, ging/fiware-draco

5. Vibrobox docker images: vbox-fc, vcloud-fc, vbot (should be build, no images in repo)


# starting of work

1. open / root dir / of the project,  
e.g. root of the project = git repo `VibroBox/fiware_components` root dir =` H:\Work\Git\vbx_fiware_comps`

2. open unux shell in the root dir of the git project,  
e.g. in windows file manager call `git bash` from context menu of the root dir

3. clone fiware_components repo, e.g.  
```
git clone https://github.com/VibroBox/fiware_components/
git checkout development
```

4. clone vbot repo or extract the vibrobox_bot (vbot) archive to / vbot dir /  


# settings

1. in / vbot dir /  

1.1 put the vbot.cfg file (if distributed separately)

1.2 or rename and edit .env.prod

1.3 set variables in vbot.cfg (see vbot manual)

2. in / root dir /

2.1 put the .env file (if distributed separately)

2.2 or rename and edit .env.prod

2.3 in the .env file set the path to the / vbot dir /, two api keys and chat id


# open ports  

on windows 10  

1. run `firewall.cpl`  

2. (before creating firewall rules first deploy reset of win 10 firewall and pc restart may have been required)  

3. add incoming rule `all local ports` for `ICMPv4` (for pinging vcloud-fc)  

4. add incoming rule loacal `7797, 1026, 7896, 4041` or `1026, 4041, 7896, 7797, 8089, 8443, 5050, 9090, 27017` for TCP (for incoming vcloud-fc)  

5. check the ports are opened, e.g. `netstat -a | grep LISTEN`, `netstat -a -n -o | grep LISTEN`  

6. check the hots is pinging from vbox, e.g. `ping 10.8.0.82`, `nmap 10.8.0.82 -Pn`, `nc -vz 10.8.0.82 1026`  


# deploy vcloud-fc

in the / root dir /  

1. build and run vcloud-fc by starting docker-compose.yml:
```
# rebuild every time if any changes to vbot
docker-compose build vbot 

# rebuild every time if any changes to vcloud-fc
docker-compose build vcloud-fc 

# check running containers
docker-compose ps 

# if smth is running
docker-compose stop 

# reset containers to start from the beginning (skip to preserve container settings)
docker-compose rm # y+Enter

# start all in backgroud
docker-compose up -d 
```


2. check no errors with commands:
```
docker-compose ps #all services should be "UP" and docker-compose logs 
docker-compose logs vbot
docker-compose logs vcloud-fc
docker-compose logs | grep "something"
```

3. configure draco

3.1 open draco web interface, you may need to wait some minutes while it is starting in background
http://localhost:9090/nifi/

3.2 add three-component template for "orion-to-mongo"

3.3 set url in  draco component "NGSItoMongo -> view configuration -> properties -> Mongo URI"
mongodb://localhost:27017

3.4 run all draco components by "play" triangle icon

3.5 draco incoming can be tested by running from shell
```
touch ./notification.sh
a+x notification.sh
./notification.sh http://localhost:5050/v2/notify
```

  
4. configure and test vclou-fc  
  
4.1 you may use any existing python 3 environment (v.3.8.2 tested),  
4.2 with dependencies: requests, aiohttp, aiohttp_cors  
4.3 or set up a new one by `setup-(win)-python3-libs.sh`  
4.3.1 before that - manually download python and curl,   
4.3.2 unzip and write down paths to dirs with executables in the .sh script  
  
4.6 call with the python 3:  

4.6.1 Set up environment
conda env create -f environment.yml
conda activate fiware
python -m pip freeze # See your packages.
python -m pip install --ignore-installed aiohttp
python -m pip install --ignore-installed aiohttp_cors
conda deactivate

4.6.2 Try to run evironment...

conda activate fiware

python ./vbox_fiware_connector.py --ping

python ./vbox_fiware_connector.py --unsubscribe --subscribe --subscribe2

python ./vbox_fiware_connector.py --reg-device

python ./vbox_fiware_connector.py --send-once --test

# if there are any data files in the / root dir /
python ./vbox_fiware_connector.py --send_once
conda deactivate



```
./python382x86/python.exe ./vbox_fiware_connector.py --ping

./python382x86/python.exe ./vbox_fiware_connector.py --unsubscribe --subscribe --subscribe2

./python382x86/python.exe ./vbox_fiware_connector.py --reg-device

./python382x86/python.exe ./vbox_fiware_connector.py --send-once --test

# if there are any data files in the / root dir /
./python382x86/python.exe ./vbox_fiware_connector.py --send_once
```

# delpoy vbox-fc
  
1. build vbox-fc executable for RPi using docker from the / root dir / :  
`docker-compose -f ./docker-compose-build-vbox-fc.yml build vbox-fc-build && docker-compose -f ./docker-compose-build-vbox-fc.yml up`
  
2. prepare / target dir / at a vbox device,  
e.g. from `/home/pi/` call `mkdir ./fiware/ && chmod -R 777 ./fiware/`
  
3. copy RPi executable `vbox_fiware_connector` from / root dir /dist/ to vbox / target dir /,  
e.g. `/home/pi/fiware` and set execute permissions
  
4. cd to the dir (like `cd ./fiware`) and run the executable from vbox console, e.g:  
  
4.1 simple test on fivare-vibrobox services ping  
`./vbox_fiware_connector --ping`  
  
4.2 fast start in server-mode with default settings (no work in backgroung)  
`./vbox_fiware_connector --server`  
  
4.3 example of run-once test for specified data file path and remote host ip, with logs:  
`./vbox_fiware_connector --send-once -dp "/storage/271.2.tar.bz2" -rh 10.8.0.82 --force-update > ./vbox_fc_log.txt 2>&1`  

4.4 start in background (second line of the example - to check, third line - stop)  
```
nohup ./vbox_fiware_connector --server -dp "/storage" -rh 10.8.0.82 > ./vbox_fc_log.txt 2>&1 &
ps -aux | grep vbox_fiware_connector
ps -aux | grep vbox_fiware_connector  | awk '{print $2; system("kill -9 " $2)}'
```
or the same (do not work - saving tail process PID does not reached):  
```
nohup ./vbox_fiware_connector --server -dp "/storage" -rh 10.8.0.82 > ./vbox_fc_log.txt 2>&1 & echo $! > vbox_fc_pid.txt
ps
kill -9 `cat vbox_fc_pid.txt` && rm vbox_fc_pid.txt 
```

# debug order

6.1 General case: all containers and apps has been started, but messages do not come.
6.2 We should determine the stage on which the normal process stopped.
  
6.3 check vcloud-side:  
6.3.1 cd to / root dir /  
6.3.2 `docker-compose ps # all containers should be 'up'`
6.3.3 `docker-compose logs orion # see last errors and messages`
6.3.4 `docker-compose logs vcloud-fc # see last errors and messages`
6.3.5 `docker-compose logs vbot # see last errors and messages`
  
6.4 check vbox-side:  
6.4.1 cd to / target dir /  
6.4.2 `ps -aux | grep vbox_fiware_connector`
6.4.3 see vbox_fc_log.txt 
6.4.4 and vbox_fc_meta.json
  
6.5 check execution and write permissions set
6.6 check locall ports are opened and firewall settings is correct
6.7 check hosts and remote ports are available (remote = local from outside)

6.8 check Context broker subscriptions status with  
http `GET` request to url `http://localhost:1026/v2/subscriptions`  
with headers `Accept: application/json`, `fiware-service: vibrobox`, `fiware-servicepath: /`  

6.9 general fixing: try to restart the service with resetting gocker containers and vbot-fc app
