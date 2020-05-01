# for RPi of vbox
# download and build python in specified dir
# 2020-04-29, Ratgor, Vibrobox

# tested on vbox via Bitvise ssh
# (!) Warnings: 
# use linux-style lines ending for this file to call it
# do not forget to set execution permissoins for the file

# Manual preparation actions
# 1. Place the script in any dir and call,
# or create /home/pi/fiware and place it there.
# pi@raspberrypi:~ $ rm -rf ./fiware
# pi@raspberrypi:~ $ mkdir ./fiware && chmod -R 777 ./fiware
# pi@raspberrypi:~ $ cd ./fiware/
# pi@raspberrypi:~/fiware $ ./setup-\(linux\)-python3-portable.sh


# CONFIG
ROOT_DIR=/home/pi/fiware
TEMP_DIR=$ROOT_DIR/temp/
REMOVE_TEMP_DIR=0 
LIBFFI_URL=ftp://sourceware.org/pub/libffi/libffi-3.3.tar.gz
LIBFFI_ZIP=${LIBFFI_URL##*/}
LIBFFI_SRC=${LIBFFI_ZIP/.tar.gz/-src}
LIBFFI_DIR=${LIBFFI_ZIP/.tar.gz/-portable}
OPENSSL_URL=https://www.openssl.org/source/openssl-1.1.1g.tar.gz
OPENSSL_ZIP=${OPENSSL_URL##*/}
OPENSSL_SRC=${OPENSSL_ZIP/.tar.gz/-src}
OPENSSL_DIR=${OPENSSL_ZIP/.tar.gz/-portable}
PYTHON_URL=https://www.python.org/ftp/python/3.8.2/Python-3.8.2.tgz
PYTHON_ZIP=${PYTHON_URL##*/}
PYTHON_SRC=${PYTHON_ZIP/.tgz/-src}
PYTHON_DIR=${PYTHON_ZIP/.tgz/-portable}


# Prepare working dirs
mkdir $ROOT_DIR && chmod 777 $ROOT_DIR
mkdir $TEMP_DIR && chmod 777 $TEMP_DIR
mkdir $TEMP_DIR/$LIBFFI_SRC && chmod 777 $TEMP_DIR/$LIBFFI_SRC
mkdir $ROOT_DIR/$LIBFFI_DIR && chmod 777 $ROOT_DIR/$LIBFFI_DIR
mkdir $TEMP_DIR/$OPENSSL_SRC && chmod 777 $TEMP_DIR/$OPENSSL_SRC
mkdir $ROOT_DIR/$OPENSSL_DIR && chmod 777 $ROOT_DIR/$OPENSSL_DIR
mkdir $TEMP_DIR/$PYTHON_SRC && chmod 777 $TEMP_DIR/$PYTHON_SRC
mkdir $ROOT_DIR/$PYTHON_DIR && chmod 777 $ROOT_DIR/$PYTHON_DIR


# Download, build and inslall (portable) Libffi
cd $TEMP_DIR
wget $LIBFFI_URL
tar xavf ./$LIBFFI_ZIP -C $TEMP_DIR/$LIBFFI_SRC/
cd $LIBFFI_SRC/${LIBFFI_SRC/-src/}
./configure --prefix=$ROOT_DIR/$LIBFFI_DIR/ >& $TEMP_DIR/make-config-libffi.log
make >& $TEMP_DIR/make-build-libffi.log
make install >& $TEMP_DIR/make-install-libffi.log


# Download, build and inslall (portable) OpenSSL
cd $TEMP_DIR
wget $OPENSSL_URL
tar xavf ./$OPENSSL_ZIP -C $TEMP_DIR/$OPENSSL_SRC/
cd $OPENSSL_SRC/${OPENSSL_SRC/-src/}
./config --prefix=$ROOT_DIR/$OPENSSL_DIR/ --openssldir=$ROOT_DIR/$OPENSSL_DIR/ >& $TEMP_DIR/make-config-openssl.log
make >& $TEMP_DIR/make-build-openssl.log
make install >& $TEMP_DIR/make-install-openssl.log


# Download, build and inslall (portable) Python3
cd $TEMP_DIR
wget $PYTHON_URL
tar xavf ./$PYTHON_ZIP -C $TEMP_DIR/$PYTHON_SRC/
cd $PYTHON_SRC/${PYTHON_SRC/-src/}
./configure --prefix=$ROOT_DIR/$PYTHON_DIR/ --with-openssl=$ROOT_DIR/$OPENSSL_DIR/ CFLAGS="-I$LIBFFI_DIR/include" LDFLAGS="-L$LIBFFI_DIR/lib" >& $TEMP_DIR/make-config-python3.log
make >& $TEMP_DIR/make-build-python3.log
make install >& $TEMP_DIR/make-install-python3.log


# Install additional Python3 modules

cd $ROOT_DIR
./$PYTHON_DIR/bin/python3 -m pip install --upgrade pip wheel setuptools pyinstaller

./$PYTHON_DIR/bin/python3 -m pip install --ignore-installed requests
./$PYTHON_DIR/bin/python3 -m pip install --ignore-installed aiohttp aiohttp_cors
#./$PYTHON_DIR/bin/python3 -m pip install --ignore-installed wget
#./$PYTHON_DIR/bin/python3 -m pip install --ignore-installed paramiko
#./$PYTHON_DIR/bin/python3 -m pip install --ignore-installed lxml
#./$PYTHON_DIR/bin/python3 -m pip install --ignore-installed psutil


# Replace orginal wave lib to inport wavs in extended format
cp ./vbxlib/replace-std-Lib-wave.py ./$PYTHON_DIR/Lib/wave.py


# Post-install actions
echo Python3 portable installation complete
echo Path to executable is ./$PYTHON_DIR/bin/python3
tar -czvf python3_RPi_portable.tar.gz $ROOT_DIR
if ["$REMOVE_TEMP_DIR" == "0"] ; then
	rm -rf $TEMP_DIR
	echo temp dir has been removed
else
	echo temp dir with logs is $TEMP_DIR
fi