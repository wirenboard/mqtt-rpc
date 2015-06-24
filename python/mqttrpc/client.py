import json

import mosquitto
#~ import threading
from concurrent.futures import Future
from .protocol import MQTTRPC10Response
from jsonrpc.exceptions import JSONRPCError

from concurrent.futures._base import TimeoutError

#~ class AsyncResult(threading.Event):
    #~ def set(self, value):
        #~ self.value = value
        #~ super(AsyncResult, self).set()

class TMQTTRPCClient(object):
    def __init__(self, client):
        self.client = client
        self.counter = 0
        self.futures = {}
        self.subscribes = set()

    def on_mqtt_message(self, mosq, obj, msg):
        print msg.topic
        print msg.payload

        parts = msg.topic.split('/')
        driver_id = parts[3]
        service_id = parts[4]
        method_id = parts[5]
        client_id = parts[6]


        result = MQTTRPC10Response.from_json(msg.payload)

        future = self.futures.pop((driver_id, service_id, method_id, result._id), None)
        if future is None:
            return

        if result.error:
            future.set_exception(RuntimeError(result.error))

        future.set_result(result.result)

    def call(self, driver, service, method, params, timeout=None):
        future = self.call_async( driver, service, method, params)

        try:
            result = future.result(1E100 if timeout is None else timeout)
        except TimeoutError, err:
            # delete callback
            self.futures.pop((driver, service, method, future.packet_id), None)
            raise err
        else:
            return result



    def call_async(self, driver, service, method, params):
        self.counter += 1
        payload = {'params': params,
                   'id' : self.counter}

        result = Future()
        result.packet_id = self.counter
        self.futures[(driver, service, method, self.counter)] = result



        topic = '/rpc/v1/%s/%s/%s/%s' % (driver, service, method, self.client._client_id.replace('/','_'))

        subscribe_key = (driver, service, method)
        if subscribe_key not in self.subscribes:
            self.subscribes.add(subscribe_key)
            self.client.subscribe(topic + '/reply')



        self.client.publish(topic, json.dumps(payload))

        return result


