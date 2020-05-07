# Download and build python3-vbox-fc in specified dir for vbox RPi
# 2020-04-29, Ratgor, Vibrobox

# (!!!) the build script is outdated, 
# docker-compose-build-vbox-fc.yml + dockerfile_vbox_fiware_connector_build
# are the newer version fo the script

# tested on vbox via Bitvise ssh
# (!) Warnings: 
# use linux-style lines ending for this file to call it
# do not forget to set execution permissoins for the script

# Additional info
# http://ubuntu42.blogspot.com/2018/12/setting-up-pyhon-37-with-ssl-support.html

# Manual preparation actions
# 1.a Check CONFIG below - set dirs and pathes
# 2.a Place the script in /home/pi/ call,
# 2.b or create /home/pi/fiware, place it there and run:
# pi@raspberrypi:~ $ rm -rf ./fiware
# pi@raspberrypi:~ $ mkdir ./fiware && chmod -R 777 ./fiware
# pi@raspberrypi:~ $ cd ./fiware/
# pi@raspberrypi:~/fiware $ ./setup-\(linux\)-python3-portable.sh


# CONFIG
ROOT_DIR=/home/pi/fiware
TEMP_DIR=$ROOT_DIR/temp
REMOVE_ROOT_DIR=0
REMOVE_TEMP_DIR=0 
CREATE_DIRS=0
INSTALL_LIBFFI=0
INSTALL_BZIP2=0
INSTALL_OPENSSL=0
INSTALL_PYTHON=0
INSTALL_PYTHON_MODULES=0
ARCHIVE_ALL=0

LIBFFI_URL=ftp://sourceware.org/pub/libffi/libffi-3.3.tar.gz
LIBFFI_ZIP=${LIBFFI_URL##*/}
LIBFFI_VER=${LIBFFI_ZIP/.tar.gz/}
LIBFFI_SRC=${TEMP_DIR}/${LIBFFI_VER}-src
LIBFFI_DIR=${ROOT_DIR}/${LIBFFI_VER}-portable

BZIP2_URL=https://www.sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz
BZIP2_ZIP=${BZIP2_URL##*/}
BZIP2_VER=${BZIP2_ZIP/.tar.gz/}
BZIP2_SRC=${TEMP_DIR}/${BZIP2_VER}-src
BZIP2_DIR=${ROOT_DIR}/${BZIP2_VER}-portable

OPENSSL_URL=https://www.openssl.org/source/openssl-1.1.1g.tar.gz
OPENSSL_ZIP=${OPENSSL_URL##*/}
OPENSSL_VER=${OPENSSL_ZIP/.tar.gz/}
OPENSSL_SRC=${TEMP_DIR}/${OPENSSL_VER}-src
OPENSSL_DIR=${ROOT_DIR}/${OPENSSL_VER}-portable

PYTHON_URL=https://www.python.org/ftp/python/3.8.2/Python-3.8.2.tgz
PYTHON_ZIP=${PYTHON_URL##*/}
PYTHON_VER=${PYTHON_ZIP/.tgz/}
PYTHON_SRC=${TEMP_DIR}/${PYTHON_VER}-src
PYTHON_DIR=${ROOT_DIR}/${PYTHON_VER}-portable



# Prepare working dirs
if [ $REMOVE_ROOT_DIR = 1 ] ; then
	rm -rf $ROOT_DIR
	echo root dir $ROOT_DIR has been removed
else
	echo root dir is $ROOT_DIR
fi

if [ $CREATE_DIRS = 1 ]; then
[[ ! -d $ROOT_DIR ]] && mkdir $ROOT_DIR && chmod -R 777 $ROOT_DIR
[[ ! -d $TEMP_DIR ]] && mkdir $TEMP_DIR && chmod -R 777 $TEMP_DIR
[[ ! -d $LIBFFI_SRC ]] && mkdir $LIBFFI_SRC && chmod -R 777 $LIBFFI_SRC
[[ ! -d $LIBFFI_DIR ]] && mkdir $LIBFFI_DIR && chmod -R 777 $LIBFFI_DIR
[[ ! -d $BZIP2_SRC ]] && mkdir $BZIP2_SRC && chmod -R 777 $ZIP2_SRC
[[ ! -d $BZIP2_DIR ]] && mkdir $BZIP2_DIR && chmod -R 777 $BZIP2_DIR
[[ ! -d $OPENSSL_SRC ]] && mkdir $OPENSSL_SRC && chmod -R 777 $OPENSSL_SRC
[[ ! -d $OPENSSL_DIR ]] && mkdir $OPENSSL_DIR && chmod -R 777 $OPENSSL_DIR
[[ ! -d $PYTHON_SRC ]] && mkdir $PYTHON_SRC && chmod -R 777 $PYTHON_SRC
[[ ! -d $PYTHON_DIR ]] && mkdir $PYTHON_DIR && chmod -R 777 $PYTHON_DIR
fi

# Download, build and inslall (portable) Libffi
if [ $INSTALL_LIBFFI = 1 ]; then
cd $TEMP_DIR
wget $LIBFFI_URL
tar xavf ./$LIBFFI_ZIP -C $LIBFFI_SRC
cd $LIBFFI_SRC/$LIBFFI_VER
./configure CFLAGS=-fPIC --prefix=$LIBFFI_DIR >& $TEMP_DIR/make-config-libffi.log
make >& $TEMP_DIR/make-build-libffi.log
make install >& $TEMP_DIR/make-install-libffi.log
fi

# Download, build and inslall (portable) BZip2
if [ $INSTALL_BZIP2 = 1 ]; then
cd $TEMP_DIR
wget $BZIP2_URL
tar xavf ./$BZIP2_ZIP -C $BZIP2_SRC
cd $BZIP2_SRC/$BZIP2_VER
./config shared CFLAGS=-fPIC --prefix=$BZIP2_DIR >& $TEMP_DIR/make-config-bzip2.log
make >& $TEMP_DIR/make-build-bzip2.log
make altinstall >& $TEMP_DIR/make-install-bzip2.log
fi

# Download, build and inslall (portable) OpenSSL
if [ $INSTALL_OPENSSL = 1 ]; then
cd $TEMP_DIR
wget $OPENSSL_URL
tar xavf ./$OPENSSL_ZIP -C $OPENSSL_SRC
cd $OPENSSL_SRC/$OPENSSL_VER
./config shared CFLAGS=-fPIC --prefix=$OPENSSL_DIR --openssldir=$OPENSSL_DIR >& $TEMP_DIR/make-config-openssl.log
make >& $TEMP_DIR/make-build-openssl.log
make altinstall >& $TEMP_DIR/make-install-openssl.log
fi

# Download, build and inslall (portable) Python3
if [ $INSTALL_PYTHON = 1 ]; then
cd $TEMP_DIR
wget $PYTHON_URL
tar xavf ./$PYTHON_ZIP -C $PYTHON_SRC
cd $PYTHON_SRC/$PYTHON_VER
#(!) is final for docker:
#./configure CFLAGS="-I${OPENSSL_DIR}/include" LDFLAGS="-L${OPENSSL_DIR}/lib -Wl,-rpath=${PYTHON_DIR}/lib" --enable-shared --prefix=${PYTHON_DIR} --with-openssl=${OPENSSL_DIR}

#(?) is for max-test:
./configure CFLAGS="-fPIC -I${LIBFFI_DIR}/include -I${OPENSSL_DIR}/include -I${BZIP2_DIR}/include" LDFLAGS="-L${LIBFFI_DIR}/lib -R${LIBFFI_DIR}/lib -L${OPENSSL_DIR}/lib -R${OPENSSL_DIR}/lib -L${BZIP2_DIR}/lib -R${BZIP2_DIR}/lib -Wl,-rpath=${PYTHON_DIR}/lib" --enable-shared --enable-optimizations --prefix=${PYTHON_DIR} --with-openssl=${OPENSSL_DIR} > ${TEMP_DIR}/make-config-python3.log 2>&1 &

$OPENSSL_DIR/ >& $TEMP_DIR/make-config-python3.log
make >& $TEMP_DIR/make-build-python3.log
make altinstall >& $TEMP_DIR/make-install-python3.log
fi

# Install additional Python3 modules

if [ $INSTALL_PYTHON_MODULES = 1 ]; then
cd $ROOT_DIR
$PYTHON_DIR/bin/python3 -m pip install --upgrade pip wheel setuptools pyinstaller

$PYTHON_DIR/bin/python3 -m pip install --ignore-installed requests
$PYTHON_DIR/bin/python3 -m pip install --ignore-installed aiohttp aiohttp_cors
fi

# Post-install actions
echo Python3 portable installation complete
echo Path to executable is $PYTHON_DIR/bin/python3
if [ $ARCHIVE_ALL = 1 ]; then
tar -czvf python3_RPi_portable.tar.gz $ROOT_DIR
fi
if [ $REMOVE_TEMP_DIR = 1 ] ; then
	rm -rf $TEMP_DIR
	echo temp dir $TEMP_DIR has been removed
else
	echo temp dir is $TEMP_DIR, logs are included
fi