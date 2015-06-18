""" Dispatcher is used to add methods (functions) to the server.

For usage examples see :meth:`Dispatcher.add_method`

"""
import collections


class Dispatcher(collections.MutableMapping):

    """ Dictionary like object which maps method_name to method."""

    def __init__(self, prototype=None):
        """ Build method dispatcher.

        Parameters
        ----------
        prototype : object or dict, optional
            Initial method mapping.

        Examples
        --------

        Init object with method dictionary.

        >>> Dispatcher({("arithmetics", "sum"): lambda a, b: a + b})
        None

        """
        self.method_map = dict()

        if prototype is not None:
            self.build_method_map(prototype)

    def __getitem__(self, key):
        return self.method_map[key]

    def __setitem__(self, key, value):
        if isinstance(key, tuple) or isinstance(key, list):
            if len(key) == 2:
                self.method_map[key] = value
                return


        raise RuntimeError("key must be tuple or list of (service, method)")

    def __delitem__(self, key):
        del self.method_map[key]

    def __len__(self):
        return len(self.method_map)

    def __iter__(self):
        return iter(self.method_map)

    def __repr__(self):
        return repr(self.method_map)

    def add_class(self, cls):
        self.build_method_map(cls())

    def add_object(self, obj):
        self.build_method_map(obj)

    def add_dict(self, dict):
        self.build_method_map(dict)

    def add_method(self, f, service=None, name=None):
        """ Add a method to the dispatcher.

        Parameters
        ----------
        f : callable
            Callable to be added.
        service : str, optional
            Service to register (the default is method class name, or 'main' if none)
        name : str, optional
            Name to register (the default is function **f** name)

        Notes
        -----
        When used as a decorator keeps callable object unmodified.

        Examples
        --------

        Use as method

        >>> d = Dispatcher()
        >>> d.add_method(lambda a, b: a + b, service="arith", name="sum")
        <function __main__.<lambda>>

        Or use as decorator

        >>> d = Dispatcher()
        >>> @d.add_method
            def mymethod(*args, **kwargs):
                print(args, kwargs)

        """

        if service is None:
            if hasattr(f, 'im_class'):
                service = f.im_class.__name__
            else:
                service = 'main'

        self.method_map[(service, name or f.__name__)] = f
        return f


    def build_method_map(self, prototype):
        """ Add prototype methods to the dispatcher.

        Parameters
        ----------
        prototype : object or dict
            Initial method mapping.
            If given prototype is a dictionary then all callable objects will
            be added to dispatcher.
            If given prototype is an object then all public methods will
            be used.
        """


        if not isinstance(prototype, dict):
            service = prototype.__class__.__name__.lower() + '.'

            prototype = dict(((service, method), getattr(prototype, method))
                             for method in dir(prototype)
                             if not method.startswith('_'))

        for attr, method in prototype.items():
            if callable(method):
                self[attr] = method
