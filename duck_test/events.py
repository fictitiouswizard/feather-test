import json
import multiprocessing
import queue
import sys
import importlib
from typing import Dict, List, Callable
import inspect
from duck_test.reporters.base_reporter import BaseReporter
from duck_test.helpers import to_snake_case



class TestMessage:
    def __init__(self, module_name, class_name, test_name, additional_data=None):
        self.module_name = module_name
        self.class_name = class_name
        self.test_name = test_name
        self.additional_data = additional_data or {}

    def to_json(self):
        return json.dumps({
            'module_name': self.module_name,
            'class_name': self.class_name,
            'test_name': self.test_name,
            'additional_data': self.additional_data
        })

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(
            data['module_name'],
            data['class_name'],
            data['test_name'],
            data.get('additional_data')
        )

class EventPublisher:
    def __init__(self, queue):
        self.event_queue = queue

    def publish(self, event_type: str, correlation_id: str, **kwargs):
        self.event_queue.put((event_type, correlation_id, kwargs))

    def __getstate__(self):
        return {'event_queue': self.event_queue}

    def __setstate__(self, state):
        self.event_queue = state['event_queue']

class EventBus:
    def __init__(self, queue):
        self.event_queue = queue
        self.subscribers: Dict[str, List[Callable]] = {}
        self.reporters: List[BaseReporter] = []

    def load_reporter(self, reporter_name, **kwargs):
        if isinstance(reporter_name, str):
            # Try to load from __main__ first
            main_module = sys.modules['__main__']
            reporter_class = getattr(main_module, reporter_name, None)
            
            if reporter_class is None:
                # If not found in __main__, try duck_test.reporters
                try:
                    snake_case_name = to_snake_case(reporter_name)
                    module = importlib.import_module(f'duck_test.reporters.{snake_case_name}')
                    reporter_class = getattr(module, reporter_name)
                except (ImportError, AttributeError):
                    raise ValueError(f"Reporter '{reporter_name}' not found in __main__ or duck_test.reporters")
            
            # Convert kebab-case CLI arguments to snake_case for the reporter
            snake_case_kwargs = {key.replace('-', '_'): value for key, value in kwargs.items()}
            reporter = reporter_class(**snake_case_kwargs)
        elif isinstance(reporter_name, type) and issubclass(reporter_name, BaseReporter):
            # Convert kebab-case CLI arguments to snake_case for the reporter
            snake_case_kwargs = {key.replace('-', '_'): value for key, value in kwargs.items()}
            reporter = reporter_name(**snake_case_kwargs)
        else:
            raise ValueError("Reporter must be a string name or a BaseReporter subclass")

        self.reporters.append(reporter)
        self._subscribe_reporter(reporter)

    def _subscribe_reporter(self, reporter: BaseReporter):
        for name, method in inspect.getmembers(reporter, inspect.ismethod):
            if name.startswith('on_'):
                event_name = name[3:]
                self.subscribe(event_name, method)

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, correlation_id: str, **kwargs):
        self.event_queue.put((event_type, correlation_id, kwargs))

    def process_events(self):
        while True:
            try:
                event_type, correlation_id, kwargs = self.event_queue.get(timeout=0.1)
                print("from queue", event_type, correlation_id, kwargs)
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
        return EventPublisher(self.event_queue)

