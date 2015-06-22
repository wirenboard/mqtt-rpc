import json
import argparse
import mosquitto

#~ import threading
from concurrent.futures import Future
from mqttrpc.protocol import MQTTRPC10Response
from jsonrpc.exceptions import JSONRPCError
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
        future = self.futures.pop((driver_id, service_id, method_id, result._id))
        if future is None:
            return

        if result.error:
            future.set_exception(RuntimeError(result.error))

        future.set_result(result.result)
#~
    #~ def setup(self):
        #~ for service, method in dispatcher.iterkeys():
            #~ self.client.publish("/rpc/v1/%s/%s/%s" % (self.driver_id, service, method), "1", retain=True)
#~
            #~ self.client.subscribe("/rpc/v1/%s/%s/%s/+" % (self.driver_id, service, method))

    def call(self, driver, service, method, params, timeout=None):
        future = self.call_async( driver, service, method, params)
        return future.result(1E100 if timeout is None else timeout)

    def call_async(self, driver, service, method, params):
        self.counter += 1
        payload = {'params': params,
                   'id' : self.counter}

        result = Future()
        self.futures[(driver, service, method, self.counter)] = result



        topic = '/rpc/v1/%s/%s/%s/%s' % (driver, service, method, self.client._client_id.replace('/','_'))

        subscribe_key = (driver, service, method)
        if subscribe_key not in self.subscribes:
            self.subscribes.add(subscribe_key)
            self.client.subscribe(topic + '/reply')



        self.client.publish(topic, json.dumps(payload))

        return result



def main():
    parser = argparse.ArgumentParser(description='Sample RPC client', add_help=False)

    parser.add_argument('-h', '--host', dest='host', type=str,
                     help='MQTT host', default='localhost')

    parser.add_argument('-u', '--username', dest='username', type=str,
                     help='MQTT username', default='')

    parser.add_argument('-P', '--password', dest='password', type=str,
                     help='MQTT password', default='')

    parser.add_argument('-p', '--port', dest='port', type=int,
                     help='MQTT port', default='1883')

    args = parser.parse_args()
    client = mosquitto.Mosquitto()

    if args.username:
        client.username_pw_set(args.username, args.password)

    client.connect(args.host, args.port)
    client.loop_start()

    rpc_client = TMQTTRPCClient(client)
    client.on_message = rpc_client.on_mqtt_message

    resp =  rpc_client.call('Driver', 'main', 'foobar', {'foo':'foo', 'bar':'bar'})
    print resp




    raw_input()




if __name__ == "__main__":
    main()
