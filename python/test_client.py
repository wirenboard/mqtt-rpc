import json, time
import pprint
import argparse


try:
    import mosquitto
except ImportError:
    import paho.mqtt.client as mosquitto


from mqttrpc.client import TMQTTRPCClient
from jsonrpc.exceptions import JSONRPCError


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

    #~ resp =  rpc_client.call('Driver', 'main', 'foobar', {'foo':'foo', 'bar':'bar'})

    for i in xrange(10):
        resp =  rpc_client.call('db_logger', 'history', 'get_values', {
                    'channels': [
                        [ 'wb-w1', '00-1234566789' ],
                        [ 'wb-w1', '00' ],
                        [ 'wb-adc', 'Vin'],
                    ],

                    'timestamp' : {
                        'gt': 1434728034
                    },
                    'limit' : 60
                }, 10)

        print "got result!"
        pprint.pprint(resp)
        time.sleep(5)





if __name__ == "__main__":
    main()
