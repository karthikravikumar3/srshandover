set -ex
BINDIR=`dirname $0`
source $BINDIR/common.sh

if [ -f $SRCDIR/open5gs-setup-complete ]; then
    echo "setup already ran; not running again"
    exit 0
fi

sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:open5gs/latest
sudo apt update
sudo apt install -y open5gs
sudo cp /local/repository/etc/open5gs/* /etc/open5gs/
sudo systemctl restart open5gs-mmed
sudo systemctl restart open5gs-sgwud

#TODO: find a better method for adding subscriber info
cd $SRCDIR
wget https://raw.githubusercontent.com/open5gs/open5gs/main/misc/db/open5gs-dbctl
chmod +x open5gs-dbctl
./open5gs-dbctl add 001010123456789 00112233445566778899aabbccddeeff 63BFA50EE6523365FF14C1F45F88737D  # IMSI,K,OPC
./open5gs-dbctl type 001010123456789 1  # APN type IPV4
touch $SRCDIR/open5gs-setup-complete
