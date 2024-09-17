import json
import queue
import importlib
import traceback
from typing import Dict, List, Callable
import inspect
from feather_test.reporters.base_reporter import BaseReporter
from feather_test.utils import to_snake_case
from feather_test.utils.reporter_loader import load_reporter
from feather_test.reporters.reporter_proxy import ReporterProxy
import multiprocessing
import sys

class TestMessage:
    """
    Represents a test message containing information about a specific test.

    This class is used to encapsulate test information for communication between
    different components of the Feather Test framework.

    Attributes:
        module_name (str): The name of the module containing the test.
        class_name (str): The name of the test class.
        test_name (str): The name of the test method.
        additional_data (dict): Optional additional data associated with the test.
    """

    def __init__(self, module_name, class_name, test_name, additional_data=None):
        """
        Initialize a TestMessage instance.

        :param module_name: The name of the module containing the test.
        :param class_name: The name of the test class.
        :param test_name: The name of the test method.
        :param additional_data: Optional dictionary of additional data.
        """
        self.module_name = module_name
        self.class_name = class_name
        self.test_name = test_name
        self.additional_data = additional_data or {}

    def to_json(self):
        """
        Convert the TestMessage to a JSON string.

        :return: A JSON string representation of the TestMessage.
        """
        return json.dumps({
            'module_name': self.module_name,
            'class_name': self.class_name,
            'test_name': self.test_name,
            'additional_data': self.additional_data
        })

    @classmethod
    def from_json(cls, json_str):
        """
        Create a TestMessage instance from a JSON string.

        :param json_str: A JSON string representation of a TestMessage.
        :return: A new TestMessage instance.
        """
        data = json.loads(json_str)
        return cls(
            data['module_name'],
            data['class_name'],
            data['test_name'],
            data.get('additional_data')
        )

class EventPublisher:
    """
    Responsible for publishing events to the event queue.

    This class provides a simple interface for publishing events that can be
    consumed by event subscribers.

    Attributes:
        event_queue (multiprocessing.Queue): A queue for storing published events.
    """

    def __init__(self, queue):
        """
        Initialize an EventPublisher instance.

        :param queue: A multiprocessing.Queue instance for storing events.
        """
        self.queue = queue

    def publish(self, event_type: str, correlation_id: str, **kwargs):
        """
        Publish an event to the event queue.

        :param event_type: The type of the event being published.
        :param correlation_id: A unique identifier to correlate related events.
        :param kwargs: Additional keyword arguments associated with the event.
        """
        print(f"Publishing event: {event_type}")
        self.queue.put((event_type, correlation_id, kwargs))

class ReporterProcess:
    def __init__(self, reporter_class_or_instance, *args, **kwargs):
        self.reporter_class_or_instance = reporter_class_or_instance
        self.args = args
        self.kwargs = kwargs
        self.event_queue = multiprocessing.Queue()
        self.stdout_queue = multiprocessing.Queue()
        self.process = None

    def start(self):
        self.process = multiprocessing.Process(target=self._run)
        self.process.start()

    def _run(self):
        try:
            # Redirect stdout and stderr to the stdout_queue
            sys.stdout = StdoutRedirector(self.stdout_queue)
            sys.stderr = StdoutRedirector(self.stdout_queue)

            if callable(self.reporter_class_or_instance):
                reporter = self.reporter_class_or_instance(*self.args, **self.kwargs)
            else:
                reporter = self.reporter_class_or_instance

            print(f"Reporter process started: {reporter.__class__.__name__}")

            while True:
                try:
                    event = self.event_queue.get(timeout=1)
                    if event is None:
                        break
                    event_type, correlation_id, kwargs = event
                    if hasattr(reporter, event_type):
                        getattr(reporter, event_type)(correlation_id=correlation_id, **kwargs)
                    else:
                        print(f"Warning: {reporter.__class__.__name__} has no method {event_type}")
                except multiprocessing.queues.Empty:
                    continue
                except Exception as e:
                    print(f"Error in reporter process: {e}")
                    traceback.print_exc()

            print(f"Reporter process stopping: {reporter.__class__.__name__}")
        except Exception as e:
            print(f"Error initializing reporter: {e}")
            traceback.print_exc()
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

    def send_event(self, event_type, correlation_id, **kwargs):
        if self.process and self.process.is_alive():
            try:
                self.event_queue.put((event_type, correlation_id, kwargs))
            except BrokenPipeError:
                print(f"BrokenPipeError: Reporter process may have terminated unexpectedly")
        else:
            print(f"Warning: Attempted to send event to terminated reporter process")

    def stop(self):
        if self.process and self.process.is_alive():
            try:
                self.event_queue.put(None)
                self.process.join(timeout=5)
                if self.process.is_alive():
                    print(f"Warning: Reporter process did not terminate gracefully, forcing termination")
                    self.process.terminate()
            except Exception as e:
                print(f"Error stopping reporter process: {e}")

class StdoutRedirector:
    def __init__(self, queue):
        self.queue = queue

    def write(self, msg):
        self.queue.put(msg)

    def flush(self):
        sys.__stdout__.flush()

class EventBus:
    """
    Manages event subscriptions and dispatches events to appropriate subscribers.

    This class serves as the central hub for the event-driven architecture in Feather Test.
    It allows components to subscribe to specific event types and handles the distribution
    of events to these subscribers.

    Attributes:
        event_queue (multiprocessing.Queue): A queue for storing published events.
        subscribers (Dict[str, List[Callable]]): A dictionary mapping event types to lists of subscriber callbacks.
        reporters (List[BaseReporter]): A list of reporter instances for handling test events.
    """

    def __init__(self):
        self.reporters: Dict[str, ReporterProcess] = {}
        self.event_queue = multiprocessing.Queue()
        self.event_publisher = EventPublisher(self.event_queue)
        self.is_running = False

    def load_reporter(self, reporter_name, *args, **kwargs):
        from feather_test.utils.reporter_loader import load_reporter
        reporter_class_or_instance = load_reporter(reporter_name)
        if reporter_class_or_instance:
            reporter_process = ReporterProcess(reporter_class_or_instance, *args, **kwargs)
            self.reporters[reporter_name] = reporter_process
            reporter_process.start()
            print(f"Reporter loaded and started: {reporter_name}")
        else:
            print(f"Failed to load reporter: {reporter_name}")

    def start(self):
        self.is_running = True
        while self.is_running:
            try:
                # Handle stdout from all reporters
                for reporter in self.reporters.values():
                    while True:
                        try:
                            stdout_msg = reporter.stdout_queue.get_nowait()
                            sys.stdout.write(stdout_msg)
                            sys.stdout.flush()
                        except multiprocessing.queues.Empty:
                            break

                # Handle events
                event = self.event_queue.get(timeout=0.1)
                event_type, correlation_id, kwargs = event
                for reporter in self.reporters.values():
                    reporter.send_event(event_type, correlation_id, **kwargs)
            except multiprocessing.queues.Empty:
                continue
            except Exception as e:
                print(f"Error in EventBus: {e}")
                traceback.print_exc()

    def stop(self):
        self.is_running = False
        for reporter_name, reporter in self.reporters.items():
            print(f"Stopping reporter: {reporter_name}")
            reporter.stop()

    def get_event_publisher(self):
        return self.event_publisher

    def __del__(self):
        self.stop()

