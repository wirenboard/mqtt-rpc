import json

try:
    import mosquitto
except ImportError:
    import paho.mqtt.client as mosquitto

import threading
#~ from concurrent.futures import Future
from .protocol import MQTTRPC10Response
from jsonrpc.exceptions import JSONRPCError

#~ from concurrent.futures._base import TimeoutError

class TimeoutError(Exception):
    pass

class MQTTRPCError(Exception):
    """ Represents error raised by server """
    def __init__(self, message, code, data):
        super(MQTTRPCError, self).__init__("%s [%d]: %s" % (message, code, data))
        self.rpc_message = message
        self.code = code
        self.data = data

class AsyncResult(object):
    def __init__(self):
        self._event = threading.Event()
        self._result = None
        self._exception = None

    def set_result(self, result):
        self._result = result
        self._event.set()

    def set_exception(self, exception):
        self._exception = exception
        self._event.set()

    def _get_result(self):
        if self._exception:
            raise self._exception
        else:
            return self._result
    def result(self, timeout=None):
        if self._event.wait(timeout):
            return self._get_result()
        else:
            raise TimeoutError()

    def exception(self, timeout=None):
        if self._event.wait(timeout):
            return self._exception
        else:
            raise TimeoutError()


class TMQTTRPCClient(object):
    def __init__(self, client):
        self.client = client
        self.counter = 0
        self.futures = {}
        self.subscribes = set()
        self.rpc_client_id = self.client._client_id.replace('/','_')

    def on_mqtt_message(self, mosq, obj, msg):
        """ return True if the message was indeed an rpc call"""

        if not mosquitto.topic_matches_sub('/rpc/v1/+/+/+/%s/reply' % self.rpc_client_id, msg.topic):
            return


        parts = msg.topic.split('/')
        driver_id = parts[3]
        service_id = parts[4]
        method_id = parts[5]
        client_id = parts[6]


        result = MQTTRPC10Response.from_json(msg.payload.decode('utf8'))

        future = self.futures.pop((driver_id, service_id, method_id, result._id), None)
        if future is None:
            return True

        if result.error:
            future.set_exception(MQTTRPCError(result.error['message'], result.error['code'], result.error['data']))

        future.set_result(result.result)

        return True

    def call(self, driver, service, method, params, timeout=None):
        future = self.call_async( driver, service, method, params)

        try:
            result = future.result(1E100 if timeout is None else timeout)
        except TimeoutError as err:
            # delete callback
            self.futures.pop((driver, service, method, future.packet_id), None)
            raise err
        else:
            return result



    def call_async(self, driver, service, method, params):
        self.counter += 1
        payload = {'params': params,
                   'id' : self.counter}

        result = AsyncResult()
        result.packet_id = self.counter
        self.futures[(driver, service, method, self.counter)] = result



        topic = '/rpc/v1/%s/%s/%s/%s' % (driver, service, method, self.rpc_client_id)

        subscribe_key = (driver, service, method)
        if subscribe_key not in self.subscribes:
            self.subscribes.add(subscribe_key)
            self.client.subscribe(topic + '/reply')



        self.client.publish(topic, json.dumps(payload))

        return result


