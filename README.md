
Идея такая: сервер подписывается на топик с каким-то общим префиксом, например, /rpc/v1/wb-rules/+/+/+
здесь wb-rules - имя приложения,
а префикс /rpc/v1/, полезен, чтобы проще было рассмотреть все доступные RPC-сервисы в системе.

Плюсы соответствуют, по порядку -
1. Имя сервиса. Соответствует, например, имени класса с методами в коде сервера.
2. Имя метода.
3. Идентификатор клиента (можно использовать mqtt client id, если он уникальный, или просто сгенерить что-то рандомное, например, UUIDv4). Клиент подписывается на /rpc/v1/wb-rules/+/+/свой_id/reply, чтобы получать ответы на свои RPC-запросы.


Driver announce method presense by publishing retained message to the following topic:

/rpc/v1/<driver>/<service>/<method>

As the message format is yet to be standartized, drivers should publish "1" to this topic.


Клиент отправляет посылку вида
{
  "id": "1234",
  "params": [
    {"A": 1, "B": 2}
  ]
}

Здесь "id" - идентификатор транзакции. Для простоты реализации сейчас это должна быть строка, являющаяся десятичным представлением 64-битного беззнакового значения. Спецификация JSON-RPC разрешает использование любой строки, но вышеназванное ограничение немного упрощает Go-реализацию, т.к. стандартный пакет net/rpc использует 64-битные идентификаторы транзакций. Использование числовых значений вместо строк - не очень, т.к. JSON'овый Number - это double, и все значения uint64 он вместить не способен.
Зачем вообще нужен идентификатор транзакции: допустим, делается несколько запросов GetValue(name) с разным значением параметра name. Запросы обрабатываются асинхронно и ответы могут придти в разном порядке. Возвращается просто число. Как клиенту отличить возвращаемые значения для разных name? Добавлять входные параметры в ответ было бы менее практичным и несовместимым с неидемпотентными операциями.
Если использовать идентификатор транзакции в топике, то это приведёт к необходимости subscribe + unsubscribe на каждом RPC-запросе. Subscribe и unsubscribe в MQTT реализованы по аналогии с QoS1 - с подтверждением: SUBSCRIBE - SUBACK, UNSUBSCRIBE-UNSUBACK, так что избыточного MQTT-трафика  выйдет порядочно.

params - список параметров. Особенность Go-реализации сервера (идея стырена с net/rpc/jsonrpc) состоит в том, что Go-методы принимают только один параметр, являющийся JSON-объектом. Вообще же параметров может быть сколько угодно, в том числе и 0.

Сервер отправляет ответ на топик, по которому пришёл запрос, с добавлением в конце /reply. Т.е., если, например, запрос был по топику
/rpc/v1/Driver/Arith/Multiply/b692040b, ответ придёт /rpc/v1/Driver/Arith/Multiply/b692040b/reply

Ответ в случае успеха выглядит как
{ "id": "1234", "result": 42, "error": null }
"id" должен соответствовать идентификатору запроса.
"result" может быть любым JSON-значением (числом, строкой, объектом, массивом...)
Поле "error" должно присутствовать и иметь значение null.

В случае ошибки ответ имеет структуру
{ "id": "1234", "result": null, "error":  "divide by zero" }

"id" должен соответствовать идентификатору запроса.
"result" должен иметь значение null
"error" должен содержать сообщение об ошибке.

Во всех случаях используется строгий стандартный JSON, т.е. комментарии не поддерживаются и все ключи объектов должны быть в кавычках. Отдельно стоит обратить внимание на то, что значения Inf и NaN в JSON не кодируются.
