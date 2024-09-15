import unittest
import multiprocessing
import importlib
import uuid
import time
from duck_test.events import EventBus, TestMessage
import queue
from multiprocessing import Pool, Manager
from duck_test.test_server import TestServer


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
    def __init__(self, processes=None, reporters=None):
        self.processes = processes or multiprocessing.cpu_count()
        self.manager = multiprocessing.Manager()
        self.event_queue = self.manager.Queue()
        self.event_bus = EventBus(self.event_queue)
        self.event_publisher = self.event_bus.get_publisher()
        self.test_server = TestServer(self.processes, self.event_queue)
        self.test_loader = unittest.TestLoader()
        self.run_correlation_id = str(uuid.uuid4())

        if reporters:
            for reporter in reporters:
                self.event_bus.load_reporter(reporter)

    def discover_and_run(self, start_dir, pattern='test*.py', top_level_dir=None):
        suite = self.test_loader.discover(start_dir, pattern, top_level_dir)
        return self.run(suite)

    def run(self, test_suite):
        self._enqueue_tests(test_suite)
        
        self.event_processor = multiprocessing.Process(target=self.event_bus.process_events)
        self.event_processor.start()

        self.event_publisher.publish('test_run_start', self.run_correlation_id, run_id=self.run_correlation_id)

        self.test_server.start()

        self.event_publisher.publish('test_run_end', self.run_correlation_id, run_id=self.run_correlation_id)

        self._process_remaining_events()

    def _enqueue_tests(self, suite):
        if isinstance(suite, unittest.TestSuite):
            for test in suite:
                self._enqueue_tests(test)
        else:
            self.test_server.add_test(TestMessage(
                module_name=suite.__class__.__module__,
                class_name=suite.__class__.__name__,
                test_name=suite._testMethodName
            ))

    def _process_remaining_events(self):
        # Wait for a short time to allow remaining events to be processed
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

