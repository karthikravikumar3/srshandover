set -ex
BINDIR=`dirname $0`
source $BINDIR/common.sh

if [ -f $SRCDIR/srs-setup-complete ]; then
    echo "setup already ran; not running again"
    exit 0
fi

cd $SRCDIR
git clone $SRS_REPO srsran
cd srsran
mkdir build
cd build
cmake ../
make -j `nproc`
sudo make install
sudo ldconfig
sudo srsran_install_configs.sh service
sudo cp /local/repository/etc/srsran/* /etc/srsran/

touch $SRCDIR/srs-setup-complete
