import unittest
import multiprocessing
from typing import Dict, List, Callable
import queue
import concurrent.futures
import importlib
import inspect
import uuid
import time
import sys

class BaseReporter:
    def on_test_run_start(self, correlation_id, **kwargs): pass
    def on_test_run_end(self, correlation_id, **kwargs): pass
    def on_test_start(self, correlation_id, **kwargs): pass
    def on_test_end(self, correlation_id, **kwargs): pass
    def on_test_success(self, correlation_id, **kwargs): pass
    def on_test_error(self, correlation_id, **kwargs): pass
    def on_test_failure(self, correlation_id, **kwargs): pass

class DefaultReporter(BaseReporter):
    def on_test_run_start(self, correlation_id, **kwargs):
        print(f"Test run started (Run ID: {kwargs.get('run_id', correlation_id)})")

    def on_test_run_end(self, correlation_id, **kwargs):
        print(f"Test run ended (Run ID: {kwargs.get('run_id', correlation_id)})")

    def on_test_start(self, correlation_id, **kwargs):
        print(f"Starting test: {kwargs.get('test_name')} (Test ID: {correlation_id})")

    def on_test_end(self, correlation_id, **kwargs):
        print(f"Ending test: {kwargs.get('test_name')} (Test ID: {correlation_id})")

    def on_test_success(self, correlation_id, **kwargs):
        print(f"Test succeeded: {kwargs.get('test_name')} (Test ID: {correlation_id})")

    def on_test_error(self, correlation_id, **kwargs):
        print(f"Test error: {kwargs.get('test_name')} - {kwargs.get('error')} (Test ID: {correlation_id})")

    def on_test_failure(self, correlation_id, **kwargs):
        print(f"Test failed: {kwargs.get('test_name')} - {kwargs.get('failure')} (Test ID: {correlation_id})")

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

    def load_reporter(self, reporter_name: str):
        try:
            module = importlib.import_module(f"reporters.{reporter_name}")
            reporter_class = getattr(module, f"{reporter_name.capitalize()}Reporter")
            reporter = reporter_class()
            self.reporters.append(reporter)
            self._subscribe_reporter(reporter)
        except (ImportError, AttributeError):
            print(f"Failed to load reporter: {reporter_name}. Using DefaultReporter.")
            self.reporters.append(DefaultReporter())
            self._subscribe_reporter(self.reporters[-1])

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
        correlation_id = getattr(test, 'correlation_id', str(uuid.uuid4()))
        setattr(test, 'correlation_id', correlation_id)
        self.event_publisher.publish('test_start', correlation_id, test_name=test._testMethodName)

    def stopTest(self, test):
        super().stopTest(test)
        correlation_id = getattr(test, 'correlation_id')
        self.event_publisher.publish('test_end', correlation_id, test_name=test._testMethodName)

    def addSuccess(self, test):
        super().addSuccess(test)
        correlation_id = getattr(test, 'correlation_id')
        self.event_publisher.publish('test_success', correlation_id, test_name=test._testMethodName)

    def addError(self, test, err):
        super().addError(test, err)
        correlation_id = getattr(test, 'correlation_id')
        self.event_publisher.publish('test_error', correlation_id, test_name=test._testMethodName, error=str(err))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        correlation_id = getattr(test, 'correlation_id')
        self.event_publisher.publish('test_failure', correlation_id, test_name=test._testMethodName, failure=str(err))

class EventDrivenTestRunner:
    def __init__(self, event_bus, processes=None, reporters=None, verbosity=1):
        self.event_bus = event_bus
        self.event_processor = None
        self.processes = processes or multiprocessing.cpu_count()
        self.test_loader = unittest.TestLoader()
        self.run_correlation_id = str(uuid.uuid4())
        self.result = None
        self.verbosity = verbosity
        
        if reporters:
            for reporter in reporters:
                self.event_bus.load_reporter(reporter)
        else:
            self.event_bus.load_reporter('default')

    def discover_and_run(self, start_dir, pattern='test*.py', top_level_dir=None):
        suite = self.test_loader.discover(start_dir, pattern, top_level_dir)
        return self.run(suite)

    def run(self, test):
        self.event_processor = multiprocessing.Process(target=self.event_bus.process_events)
        self.event_processor.start()

        self.event_bus.publish('test_run_start', self.run_correlation_id, run_id=self.run_correlation_id)

        self.result = EventDrivenTestResult(self.event_bus.get_publisher())

        with concurrent.futures.ProcessPoolExecutor(max_workers=self.processes) as executor:
            futures = list(self._create_futures(executor, test))
            for future in concurrent.futures.as_completed(futures):
                test_result = future.result()
                self._accumulate_results(test_result)

        self.event_bus.publish('test_run_end', self.run_correlation_id, run_id=self.run_correlation_id)

        self._process_remaining_events()

        return self.result

    def _create_futures(self, executor, test):
        if isinstance(test, unittest.TestSuite):
            for t in test:
                yield from self._create_futures(executor, t)
        else:
            yield executor.submit(self._run_test, test.__class__, test._testMethodName, self.event_bus.get_publisher(), self.run_correlation_id)

    @staticmethod
    def _run_test(test_class, test_method_name, event_publisher, run_correlation_id):
        test = test_class(test_method_name)
        test.event_publisher = event_publisher
        test.run_correlation_id = run_correlation_id
        result = EventDrivenTestResult(event_publisher)
        test(result)
        return result

    def _accumulate_results(self, test_result):
        if self.result is None:
            self.result = test_result
        else:
            self.result.testsRun += test_result.testsRun
            self.result.failures.extend(test_result.failures)
            self.result.errors.extend(test_result.errors)
            self.result.skipped.extend(test_result.skipped)
            self.result.expectedFailures.extend(test_result.expectedFailures)
            self.result.unexpectedSuccesses.extend(test_result.unexpectedSuccesses)

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

