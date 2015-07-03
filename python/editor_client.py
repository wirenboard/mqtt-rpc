import client
import mosquitto


def main():
    mqttClient = mosquitto.Mosquitto()
    mqttClient.connect("localhost", 1883)
    mqttClient.loop_start()

    rpc_client = client.TMQTTRPCClient(mqttClient)
    mqttClient.on_message = rpc_client.on_mqtt_message

    resp = rpc_client.call('wbrules', 'Editor', 'List', {'path': '/'})
    print resp

    raw_input()

if __name__ == "__main__":
    main()