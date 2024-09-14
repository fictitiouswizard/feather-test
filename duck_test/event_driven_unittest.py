import unittest
import multiprocessing
from typing import Dict, List, Callable, Union
import concurrent.futures
import importlib
import inspect
import uuid
import time
import sys
import queue
import re
from duck_test.reporters.base_reporter import BaseReporter

def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class EventPublisher:
    def __init__(self, queue):
        self.event_queue = queue

    def publish(self, event_type: str, correlation_id: str, **kwargs):
        self.event_queue.put((event_type, correlation_id, kwargs))

class EventBus:
    def __init__(self):
        self.event_queue = multiprocessing.Manager().Queue()
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
            
            reporter = reporter_class(**kwargs)
        elif isinstance(reporter_name, type) and issubclass(reporter_name, BaseReporter):
            reporter = reporter_name(**kwargs)
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

class EventDrivenTestResult(unittest.TestResult):
    def __init__(self, event_publisher):
        super().__init__()
        self.event_publisher = event_publisher

    def startTest(self, test):
        super().startTest(test)
        self.event_publisher.publish('test_start', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name)

    def stopTest(self, test):
        super().stopTest(test)
        self.event_publisher.publish('test_end', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name)

    def addSuccess(self, test):
        super().addSuccess(test)
        self.event_publisher.publish('test_success', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name)

    def addError(self, test, err):
        super().addError(test, err)
        self.event_publisher.publish('test_error', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name,
                                     error=str(err))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.event_publisher.publish('test_failure', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name,
                                     failure=str(err))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.event_publisher.publish('test_skip', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name,
                                     reason=reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.event_publisher.publish('test_expected_failure', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name,
                                     error=str(err))

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.event_publisher.publish('test_unexpected_success', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name)

class EventDrivenTestRunner:
    def __init__(self, processes=None, reporters=None, verbosity=1, failfast=False, buffer=False, catch_interrupt=False):
        self.event_bus = EventBus()
        self.event_processor = None
        self.processes = processes or multiprocessing.cpu_count()
        self.test_loader = unittest.TestLoader()
        self.run_correlation_id = str(uuid.uuid4())
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        self.catch_interrupt = catch_interrupt
        
        if reporters:
            for reporter in reporters:
                if isinstance(reporter, tuple):
                    reporter_name, reporter_args = reporter
                    self.event_bus.load_reporter(reporter_name, **reporter_args)
                elif isinstance(reporter, str):
                    self.event_bus.load_reporter(reporter)
                elif isinstance(reporter, type) and issubclass(reporter, BaseReporter):
                    self.event_bus.load_reporter(reporter.__name__)
                else:
                    raise ValueError("Reporter must be a string name, a BaseReporter subclass, or a tuple of (name, args)")
        else:
            self.event_bus.load_reporter('DefaultReporter')

    def discover_and_run(self, start_dir, pattern='test*.py', top_level_dir=None):
        suite = self.test_loader.discover(start_dir, pattern, top_level_dir)
        return self.run(suite)

    def run(self, test):
        self.event_processor = multiprocessing.Process(target=self.event_bus.process_events)
        self.event_processor.start()

        self.event_bus.publish('test_run_start', self.run_correlation_id, run_id=self.run_correlation_id)

        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.processes) as executor:
                futures = list(self._create_futures(executor, test))
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.event_bus.publish('test_error', self.run_correlation_id, error=str(e))
                        if self.failfast:
                            break
        except KeyboardInterrupt:
            if not self.catch_interrupt:
                raise
            self.event_bus.publish('test_run_interrupted', self.run_correlation_id)

        self.event_bus.publish('test_run_end', self.run_correlation_id, run_id=self.run_correlation_id)

        self._process_remaining_events()

    def _create_futures(self, executor, test):
        if isinstance(test, unittest.TestSuite):
            for t in test:
                yield from self._create_futures(executor, t)
        else:
            module_name = test.__class__.__module__
            class_name = test.__class__.__name__
            yield executor.submit(self._run_test, module_name, class_name, test._testMethodName, self.event_bus.get_publisher())

    @staticmethod
    def _run_test(module_name, class_name, test_method_name, event_publisher):
        module = importlib.import_module(module_name)
        test_class = getattr(module, class_name)
        test = test_class(test_method_name)
        test.event_publisher = event_publisher
        test.run_correlation_id = str(uuid.uuid4())  # Generate a new correlation ID for each test
        test.test_name = test_method_name
        test.class_name = class_name
        test.module_name = module_name
        result = EventDrivenTestResult(event_publisher)
        test(result)

    def _process_remaining_events(self):
        time.sleep(0.5)
        self.event_bus.publish('STOP', None)
        self.event_processor.join(timeout=5)
        if self.event_processor.is_alive():
            self.event_processor.terminate()

class EventDrivenTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_publisher = None
        self.correlation_id = str(uuid.uuid4())
        self.run_correlation_id = None
        self.test_name = self._testMethodName
        self.class_name = self.__class__.__name__
        self.module_name = self.__class__.__module__

    def run(self, result=None):
        if not isinstance(result, EventDrivenTestResult):
            result = EventDrivenTestResult(self.event_publisher)
        super().run(result)

    def setUp(self):
        if self.event_publisher:
            self.event_publisher.publish('test_setup', self.correlation_id, test_name=self._testMethodName)

    def tearDown(self):
        if self.event_publisher:
            self.event_publisher.publish('test_teardown', self.correlation_id, test_name=self._testMethodName)

