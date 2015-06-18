import json
import logging
from jsonrpc.utils import is_invalid_params
from jsonrpc.exceptions import (
    JSONRPCInvalidParams,
    JSONRPCInvalidRequest,
    JSONRPCInvalidRequestException,
    JSONRPCMethodNotFound,
    JSONRPCParseError,
    JSONRPCServerError,
    JSONRPCDispatchException,
)
from protocol import MQTTRPC10Request, MQTTRPC10Response
logger = logging.getLogger(__name__)


class MQTTRPCResponseManager(object):

    """ MQTT-RPC response manager.

    Method brings syntactic sugar into library. Given dispatcher it handles
    request (both single and batch) and handles errors.
    Request could be handled in parallel, it is server responsibility.

    :param str request_str: json string. Will be converted into
        MQTTRPC10Request

    :param dict dispather: dict<function_name:function>.

    """


    @classmethod
    def handle(cls, request_str, service_id, method_id, dispatcher):
        if isinstance(request_str, bytes):
            request_str = request_str.decode("utf-8")

        try:
            json.loads(request_str)
        except (TypeError, ValueError):
            return MQTTRPC10Response(error=JSONRPCParseError()._data)

        try:
            request = MQTTRPC10Request.from_json(request_str)
        except JSONRPCInvalidRequestException:
            return MQTTRPC10Response(error=JSONRPCInvalidRequest()._data)

        return cls.handle_request(request, service_id, method_id, dispatcher)

    @classmethod
    def handle_request(cls, request, service_id, method_id, dispatcher):
        """ Handle request data.

        At this moment request has correct jsonrpc format.

        :param dict request: data parsed from request_str.
        :param jsonrpc.dispatcher.Dispatcher dispatcher:

        .. versionadded: 1.8.0

        """

        def response(**kwargs):
            return MQTTRPC10Response(
                _id=request._id, **kwargs)

        try:
            method = dispatcher[(service_id, method_id)]
        except KeyError:
            output = response(error=JSONRPCMethodNotFound()._data)
        else:
            try:
                result = method(*request.args, **request.kwargs)
            except JSONRPCDispatchException as e:
                output = response(error=e.error._data)
            except Exception as e:
                data = {
                    "type": e.__class__.__name__,
                    "args": e.args,
                    "message": str(e),
                }
                if isinstance(e, TypeError) and is_invalid_params(
                        method, *request.args, **request.kwargs):
                    output = response(
                        error=JSONRPCInvalidParams(data=data)._data)
                else:
                    logger.exception("API Exception: {0}".format(data))
                    output = response(
                        error=JSONRPCServerError(data=data)._data)
            else:
                output = response(result=result)
        finally:
            if not request.is_notification:
                return output
            else:
                return []


