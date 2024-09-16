import json
import queue
import importlib
from typing import Dict, List, Callable
import inspect
from feather_test.reporters.base_reporter import BaseReporter
from feather_test.utils import to_snake_case
from feather_test.utils.reporter_loader import load_reporter

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
        self.event_queue = queue

    def publish(self, event_type: str, correlation_id: str, **kwargs):
        """
        Publish an event to the event queue.

        :param event_type: The type of the event being published.
        :param correlation_id: A unique identifier to correlate related events.
        :param kwargs: Additional keyword arguments associated with the event.
        """
        self.event_queue.put((event_type, correlation_id, kwargs))

    def __getstate__(self):
        """
        Get the state of the EventPublisher for pickling.

        :return: A dictionary containing the event_queue.
        """
        return {'event_queue': self.event_queue}

    def __setstate__(self, state):
        """
        Set the state of the EventPublisher when unpickling.

        :param state: A dictionary containing the event_queue.
        """
        self.event_queue = state['event_queue']

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

    def __init__(self, queue):
        """
        Initialize an EventBus instance.

        :param queue: A multiprocessing.Queue instance for storing events.
        """
        self.event_queue = queue
        self.subscribers: Dict[str, List[Callable]] = {}
        self.reporters: List[BaseReporter] = []

    def load_reporter(self, reporter_name, **kwargs):
        """
        Load a reporter by name and add it to the event bus.

        :param reporter_name: Name of the reporter to load
        :param kwargs: Keyword arguments to pass to the reporter's constructor
        """
        reporter = load_reporter(reporter_name, **kwargs)
        self._subscribe_reporter(reporter)
        self.reporters.append(reporter)

    def _subscribe_reporter(self, reporter: BaseReporter):
        """
        Subscribe a reporter to relevant events.

        :param reporter: An instance of BaseReporter.
        """
        for name, method in inspect.getmembers(reporter, inspect.ismethod):
            if name.startswith('on_'):
                event_name = name[3:]
                self.subscribe(event_name, method)

    def subscribe(self, event_type: str, callback: Callable):
        """
        Subscribe a callback to a specific event type.

        :param event_type: The type of event to subscribe to.
        :param callback: The callback function to be called when the event occurs.
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, correlation_id: str, **kwargs):
        """
        Publish an event to the event queue.

        :param event_type: The type of the event being published.
        :param correlation_id: A unique identifier to correlate related events.
        :param kwargs: Additional keyword arguments associated with the event.
        """
        self.event_queue.put((event_type, correlation_id, kwargs))

    def process_events(self):
        """
        Process events from the event queue and dispatch them to subscribers.

        This method runs in a loop, continuously processing events until a 'STOP' event is received.
        """
        while True:
            try:
                event_type, correlation_id, kwargs = self.event_queue.get(timeout=0.1)
                if event_type == 'STOP':
                    break
                if event_type in self.subscribers:
                    for callback in self.subscribers[event_type]:
                        # Get the parameter names of the callback
                        params = inspect.signature(callback).parameters
                        
                        # Prepare the arguments
                        args = {'correlation_id': correlation_id}

                        args.update({k: v for k, v in kwargs.items() if k in params})
                        
                        # Call the callback with the prepared arguments
                        callback(**args)
            except queue.Empty:
                continue

    def get_publisher(self):
        """
        Get an EventPublisher instance for this EventBus.

        :return: An EventPublisher instance.
        """
        return EventPublisher(self.event_queue)

