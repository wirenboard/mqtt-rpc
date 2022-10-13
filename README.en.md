MQTT-RPC
===============================
The repository contains MQTT-RPC protocol description as well as reference implementation in Python.
Other implementation include:

* C++ (as part of libwbmqtt): https://github.com/contactless/libwbmqtt/blob/master/common/mqttrpc.h
* Go (as part of wbgo package): https://github.com/contactless/wbgo/blob/master/rpc.go
* Java Script (as part of wb-mqtt-homeui): https://github.com/contactless/homeui/blob/contactless/app/scripts/services/rpc.js

MQTT-RPC Protocol Description
===============================

Driver announce method presense by publishing retained message to the following topic:

`/rpc/v1/<driver>/<service>/<method>`