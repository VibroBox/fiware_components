# fiware_components
reference components for vibrobox-fiware integration

# deploy & run 

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

./python382x86/python.exe ./vbox_fiware_connector.py --subscribe --subscribe2

./python382x86/python.exe ./vbox_fiware_connector.py --send_once