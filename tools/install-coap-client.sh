# via https://github.com/ggravlingen/pytradfri/blob/master/script/install-coap-client.sh

#!/bin/sh
git clone --depth 1 --recursive -b dtls https://github.com/obgm/libcoap.git
cd libcoap
./autogen.sh
./configure --disable-dtls --disable-tinydtls --without-submodule-tinydtls --disable-examples --disable-documentation --without-debug CFLAGS="-D COAP_DEBUG_FD=stderr"
make
make install

