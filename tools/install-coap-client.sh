# via https://github.com/ggravlingen/pytradfri/blob/master/script/install-coap-client.sh

#!/bin/sh
git clone --depth 1 --recursive -b dtls https://github.com/home-assistant/libcoap.git
cd libcoap
./autogen.sh
./configure --disable-documentation --disable-shared --without-debug CFLAGS="-D COAP_DEBUG_FD=stderr"
make
make install
