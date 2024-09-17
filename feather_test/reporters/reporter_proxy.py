import multiprocessing
import inspect
from multiprocessing import Queue, Process, Event, freeze_support

from feather_test.reporters.base_reporter import BaseReporter
import logging

logger = logging.getLogger("feather_test")

class ReporterProxy:
    def __init__(self, reporter_class_or_instance, *args, **kwargs):
        if isinstance(reporter_class_or_instance, BaseReporter):
            self.reporter_instance = reporter_class_or_instance
            self.reporter_class = type(reporter_class_or_instance)
        elif inspect.isclass(reporter_class_or_instance) and issubclass(reporter_class_or_instance, BaseReporter):
            self.reporter_class = reporter_class_or_instance
            self.reporter_instance = None  # Will be created in _run_reporter
        else:
            raise TypeError("reporter_class_or_instance must be a BaseReporter subclass or instance")

        self.args = args
        self.kwargs = kwargs
        self.queue = Queue()
        self.ready_event = Event()
        self.process = Process(target=self._run_reporter)
        self.process.start()
        self.subscribed_events = self._get_subscribed_events()
        
        # Signal that initialization is complete
        self.ready_event.set()

    def _run_reporter(self):
        # Wait for parent process to finish initialization
        self.ready_event.wait()
        
        try:
            if self.reporter_instance is None:
                self.reporter_instance = self.reporter_class(*self.args, **self.kwargs)
            while True:
                message = self.queue.get()
                if message is None:
                    break
                method_name, args, kwargs = message
                if hasattr(self.reporter_instance, method_name):
                    getattr(self.reporter_instance, method_name)(*args, **kwargs)
                else:
                    print(f"Warning: Reporter has no method named {method_name}")
        except Exception as e:
            print(f"Error in _run_reporter: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

    def _get_subscribed_events(self):
        return [
            (event_name, getattr(self.reporter_class, event_name))
            for event_name in dir(self.reporter_class)
            if event_name.startswith('on_') and callable(getattr(self.reporter_class, event_name))
        ]

    def __getattr__(self, name):
        if name in ('queue', 'process', 'reporter_class', 'reporter_instance', 'args', 'kwargs'):
            return object.__getattribute__(self, name)
        
        def proxy_method(*args, **kwargs):
            self.queue.put((name, args, kwargs))
        return proxy_method

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['queue']
        del state['process']
        del state['ready_event']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.queue = Queue()
        self.ready_event = Event()
        self.process = Process(target=self._run_reporter)
        self.process.start()
        
        # Signal that initialization is complete
        self.ready_event.set()

    def stop(self):
        self.queue.put(None)
        self.process.join()

    def __del__(self):
        if hasattr(self, 'process') and self.process.is_alive():
            self.stop()

if __name__ == '__main__':
    freeze_support()