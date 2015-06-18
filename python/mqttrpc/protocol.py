import json

from jsonrpc.utils import JSONSerializable
from jsonrpc import six
from jsonrpc.exceptions import JSONRPCError, JSONRPCInvalidRequestException


class MQTTRPCBaseRequest(JSONSerializable):

    """ Base class for JSON-RPC 1.0 and JSON-RPC 2.0 requests."""

    def __init__(self, params=None, _id=None,
                 is_notification=None):
        self.data = dict()
        self.params = params
        self._id = _id
        self.is_notification = is_notification

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if not isinstance(value, dict):
            raise ValueError("data should be dict")

        self._data = value

    @property
    def args(self):
        """ Method position arguments.

        :return tuple args: method position arguments.

        """
        return tuple(self.params) if isinstance(self.params, list) else ()

    @property
    def kwargs(self):
        """ Method named arguments.

        :return dict kwargs: method named arguments.

        """
        return self.params if isinstance(self.params, dict) else {}

    @property
    def json(self):
        return self.serialize(self.data)


class MQTTRPCBaseResponse(JSONSerializable):

    """ Base class for JSON-RPC 1.0 and JSON-RPC 2.0 responses."""

    def __init__(self, result=None, error=None, _id=None):
        self.data = dict()

        self.result = result
        self.error = error
        self._id = _id

        if self.result is None and self.error is None:
            raise ValueError("Either result or error should be used")

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if not isinstance(value, dict):
            raise ValueError("data should be dict")

        self._data = value

    @property
    def json(self):
        return self.serialize(self.data)




class MQTTRPC10Request(MQTTRPCBaseRequest):

    """ A rpc call is represented by sending a Request object to a Server.

    :param params: A Structured value that holds the parameter values to be
        used during the invocation of the method. This member MAY be omitted.
    :type params: iterable or dict

    :param _id: An identifier established by the Client that MUST contain a
        String, Number, or NULL value if included. If it is not included it is
        assumed to be a notification. The value SHOULD normally not be Null
        [1] and Numbers SHOULD NOT contain fractional parts [2].
    :type _id: str or int or None

    :param bool is_notification: Whether request is notification or not. If
        value is True, _id is not included to request. It allows to create
        requests with id = null.

    The Server MUST reply with the same value in the Response object if
    included. This member is used to correlate the context between the two
    objects.

    [1] The use of Null as a value for the id member in a Request object is
    discouraged, because this specification uses a value of Null for Responses
    with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null
    for Notifications this could cause confusion in handling.

    [2] Fractional parts may be problematic, since many decimal fractions
    cannot be represented exactly as binary fractions.

    """

    REQUIRED_FIELDS = set([])
    POSSIBLE_FIELDS = set(["params", "id"])

    @property
    def data(self):
        data = dict(
            (k, v) for k, v in self._data.items()
            if not (k == "id" and self.is_notification)
        )
        return data

    @data.setter
    def data(self, value):
        if not isinstance(value, dict):
            raise ValueError("data should be dict")

        self._data = value

    @property
    def params(self):
        return self._data.get("params")

    @params.setter
    def params(self, value):
        if value is not None and not isinstance(value, (list, tuple, dict)):
            raise ValueError("Incorrect params {0}".format(value))

        value = list(value) if isinstance(value, tuple) else value

        if value is not None:
            self._data["params"] = value

    @property
    def _id(self):
        return self._data.get("id")

    @_id.setter
    def _id(self, value):
        if value is not None and \
           not isinstance(value, six.string_types + six.integer_types):
            raise ValueError("id should be string or integer")

        self._data["id"] = value

    @classmethod
    def from_json(cls, json_str):
        data = cls.deserialize(json_str)


        if not data:
            raise JSONRPCInvalidRequestException("[] value is not accepted")

        if not isinstance(data, dict):
            raise JSONRPCInvalidRequestException(
                "Request should be an object (dict)")

        result = None
        if not cls.REQUIRED_FIELDS <= set(data.keys()) <= cls.POSSIBLE_FIELDS:
            extra = set(data.keys()) - cls.POSSIBLE_FIELDS
            missed = cls.REQUIRED_FIELDS - set(data.keys())
            msg = "Invalid request. Extra fields: {0}, Missed fields: {1}"
            raise JSONRPCInvalidRequestException(msg.format(extra, missed))

        try:
            result = MQTTRPC10Request(
                params=data.get("params"),
                _id=data.get("id"), is_notification="id" not in data,
            )
        except ValueError as e:
            raise JSONRPCInvalidRequestException(str(e))

        return  result



class MQTTRPC10Response(MQTTRPCBaseResponse):

    """ JSON-RPC response object to JSONRPC20Request.

    When a rpc call is made, the Server MUST reply with a Response, except for
    in the case of Notifications. The Response is expressed as a single JSON
    Object, with the following members:

    :param str jsonrpc: A String specifying the version of the JSON-RPC
        protocol. MUST be exactly "2.0".

    :param result: This member is REQUIRED on success.
        This member MUST NOT exist if there was an error invoking the method.
        The value of this member is determined by the method invoked on the
        Server.

    :param dict error: This member is REQUIRED on error.
        This member MUST NOT exist if there was no error triggered during
        invocation. The value for this member MUST be an Object.

    :param id: This member is REQUIRED.
        It MUST be the same as the value of the id member in the Request
        Object. If there was an error in detecting the id in the Request
        object (e.g. Parse error/Invalid Request), it MUST be Null.
    :type id: str or int or None

    Either the result member or error member MUST be included, but both
    members MUST NOT be included.

    """

    REQUIRED_FIELDS = set(['error', 'id'])
    POSSIBLE_FIELDS =  set(['error', 'id', 'result'])

    @property
    def data(self):
        data = dict((k, v) for k, v in self._data.items())
        return data

    @data.setter
    def data(self, value):
        if not isinstance(value, dict):
            raise ValueError("data should be dict")

        self._data = value

    @property
    def result(self):
        return self._data.get("result")

    @result.setter
    def result(self, value):
        if value is not None:
            if self.error is not None:
                raise ValueError("Either result or error should be used")

            self._data["result"] = value

    @property
    def error(self):
        return self._data.get("error")

    @error.setter
    def error(self, value):
        if value is not None:
            if self.result is not None:
                raise ValueError("Either result or error should be used")

            JSONRPCError(**value)
        self._data["error"] = value

    @property
    def _id(self):
        return self._data.get("id")

    @_id.setter
    def _id(self, value):
        if value is not None and \
           not isinstance(value, six.string_types + six.integer_types):
            raise ValueError("id should be string or integer")

        self._data["id"] = value






    @classmethod
    def from_json(cls, json_str):
        data = cls.deserialize(json_str)

        if not isinstance(data, dict):
            raise JSONRPCInvalidRequestException(
                "Response should be an object (dict)")

        result = None
        if not cls.REQUIRED_FIELDS <= set(data.keys()) <= cls.POSSIBLE_FIELDS:
            extra = set(data.keys()) - cls.POSSIBLE_FIELDS
            missed = cls.REQUIRED_FIELDS - set(data.keys())
            msg = "Invalid request. Extra fields: {0}, Missed fields: {1}"
            raise JSONRPCInvalidRequestException(msg.format(extra, missed))

        try:
            result = MQTTRPC10Response(
                error=data.get("error"),
                result=data.get("result"),
                _id=data.get("id")
            )
        except ValueError as e:
            raise JSONRPCInvalidRequestException(str(e))

        return  result
