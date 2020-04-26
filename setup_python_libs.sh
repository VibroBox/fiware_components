# Install libs for python embedded distribution
# 2020-04-23, Ratgor, Vibrobox

# tested on Win10x64 with GitBash (mingw64)
# manually download python and curl, 
# unzip and write down pathes to executables


CURL_DIR=curl769x86
PYTHON_DIR=python382x86
PIP_URL=https://bootstrap.pypa.io/get-pip.py


./$CURL_DIR/curl.exe $PIP_URL > ./$PYTHON_DIR/get-pip.py
./$PYTHON_DIR/python.exe ./$PYTHON_DIR/get-pip.py

# enable current pathes for finding pip module
find ./$PYTHON_DIR/ -type f -name 'python**_pth' -exec sh -c 'x="{}"; mv "$x" "${x%_pth}pth"' \;


./$PYTHON_DIR/python.exe -m pip install --upgrade pip
./$PYTHON_DIR/python.exe -m pip install --upgrade --force-reinstall setuptools
./$PYTHON_DIR/python.exe -m pip install --upgrade --force-reinstall wheel
./$PYTHON_DIR/python.exe -m pip install --upgrade --force-reinstall pyinstaller

./$PYTHON_DIR/python.exe -m pip install --ignore-installed psutil
./$PYTHON_DIR/python.exe -m pip install --ignore-installed requests
./$PYTHON_DIR/python.exe -m pip install --ignore-installed wget
./$PYTHON_DIR/python.exe -m pip install --ignore-installed paramiko
./$PYTHON_DIR/python.exe -m pip install --ignore-installed lxml
