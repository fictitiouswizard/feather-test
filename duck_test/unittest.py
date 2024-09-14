import unittest
import multiprocessing
from typing import Dict, List, Callable
import queue
import concurrent.futures


class EventPublisher:
    """
    A class for publishing events to an event queue.
    """

    def __init__(self, queue):
        """
        Initialize the EventPublisher with a queue.

        :param queue: The queue to publish events to.
        """
        self.event_queue = queue

    def publish(self, event_type: str, data: any):
        """
        Publish an event to the queue.

        :param event_type: The type of the event.
        :param data: The data associated with the event.
        """
        self.event_queue.put((event_type, data))
        print(f"Event published: {event_type}")  # Debug print

class EventBus:
    """
    A class for managing event subscriptions and publications.
    """

    def __init__(self):
        """
        Initialize the EventBus with an empty queue and subscriber dictionary.
        """
        self.event_queue = multiprocessing.Manager().Queue()
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """
        Subscribe a callback function to an event type.

        :param event_type: The type of event to subscribe to.
        :param callback: The function to call when the event occurs.
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, data: any):
        """
        Publish an event to the event queue.

        :param event_type: The type of the event.
        :param data: The data associated with the event.
        """
        self.event_queue.put((event_type, data))

    def process_events(self):
        """
        Process events from the queue and call subscribed callbacks.
        """
        while True:
            try:
                event_type, data = self.event_queue.get(timeout=0.1)
                if event_type == 'STOP':
                    break
                if event_type in self.subscribers:
                    for callback in self.subscribers[event_type]:
                        callback(data)
            except queue.Empty:
                continue

    def get_publisher(self):
        """
        Get an EventPublisher instance for this EventBus.

        :return: An EventPublisher instance.
        """
        return EventPublisher(self.event_queue)

class EventDrivenTestResult(unittest.TestResult):
    """
    A TestResult class that publishes events for test execution.
    """

    def __init__(self, event_publisher):
        """
        Initialize the EventDrivenTestResult with an event publisher.

        :param event_publisher: The EventPublisher to use for publishing events.
        """
        super().__init__()
        self.event_publisher = event_publisher

    def startTest(self, test):
        """
        Called when a test begins.

        :param test: The test case being run.
        """
        super().startTest(test)
        self.event_publisher.publish('test_start', test._testMethodName)

    def stopTest(self, test):
        """
        Called when a test finishes.

        :param test: The test case that finished.
        """
        super().stopTest(test)
        self.event_publisher.publish('test_end', test._testMethodName)

    def addSuccess(self, test):
        """
        Called when a test succeeds.

        :param test: The test case that succeeded.
        """
        super().addSuccess(test)
        self.event_publisher.publish('test_success', test._testMethodName)

    def addError(self, test, err):
        """
        Called when a test raises an error.

        :param test: The test case that raised an error.
        :param err: The error that was raised.
        """
        super().addError(test, err)
        self.event_publisher.publish('test_error', (test._testMethodName, str(err)))

    def addFailure(self, test, err):
        """
        Called when a test fails.

        :param test: The test case that failed.
        :param err: The failure details.
        """
        super().addFailure(test, err)
        self.event_publisher.publish('test_failure', (test._testMethodName, str(err)))

class EventDrivenTestRunner(unittest.TextTestRunner):
    """
    A TestRunner that uses event-driven execution and supports parallel test runs.
    """

    def __init__(self, event_bus, processes=None, *args, **kwargs):
        """
        Initialize the EventDrivenTestRunner.

        :param event_bus: The EventBus to use for event management.
        :param processes: The number of processes to use for parallel execution.
        :param args: Additional positional arguments for TextTestRunner.
        :param kwargs: Additional keyword arguments for TextTestRunner.
        """
        super().__init__(*args, **kwargs)
        self.event_bus = event_bus
        self.event_processor = None
        self.processes = processes or multiprocessing.cpu_count()
        self.test_loader = EventDrivenTestLoader()

    def discover_and_run(self, start_dir, pattern='test*.py', top_level_dir=None):
        """
        Discover and run tests from the specified directory.

        :param start_dir: The directory to start discovering tests from.
        :param pattern: The pattern to match test files.
        :param top_level_dir: The top-level directory of the project.
        :return: The EventBus after running the tests.
        """
        suite = self.test_loader.discover(start_dir, pattern, top_level_dir)
        return self.run(suite)

    def run(self, test):
        """
        Run the given test or test suite.

        :param test: The test or test suite to run.
        :return: The EventBus after running the tests.
        """
        self.event_processor = multiprocessing.Process(target=self.event_bus.process_events)
        self.event_processor.start()

        self.event_bus.publish('test_run_start', None)

        with concurrent.futures.ProcessPoolExecutor(max_workers=self.processes) as executor:
            if isinstance(test, unittest.TestSuite):
                futures = [executor.submit(self._run_test, t, self.event_bus.get_publisher()) for t in test]
                concurrent.futures.wait(futures)
            else:
                self._run_test(test, self.event_bus.get_publisher())

        self._process_remaining_events()

        self.event_bus.publish('test_run_end', None)
        self.event_bus.publish('STOP', None)

        self.event_processor.join()

        return self.event_bus

    def _process_remaining_events(self):
        """
        Process any remaining events in the event queue.
        """
        while not self.event_bus.event_queue.empty():
            try:
                event_type, data = self.event_bus.event_queue.get_nowait()
                if event_type in self.event_bus.subscribers:
                    for callback in self.event_bus.subscribers[event_type]:
                        callback(data)
            except queue.Empty:
                break

    @staticmethod
    def _run_test(test, event_publisher):
        """
        Run a single test with the given event publisher.

        :param test: The test to run.
        :param event_publisher: The EventPublisher to use for publishing events.
        """
        result = EventDrivenTestResult(event_publisher)
        test(result)

class EventDrivenTestCase(unittest.TestCase):
    """
    A TestCase class that supports event-driven execution.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the EventDrivenTestCase.

        :param args: Positional arguments for TestCase.
        :param kwargs: Keyword arguments for TestCase.
        """
        super().__init__(*args, **kwargs)
        self.event_publisher = None

    def run(self, result=None):
        """
        Run the test, ensuring an EventDrivenTestResult is used.

        :param result: The test result object to use.
        """
        if not isinstance(result, EventDrivenTestResult):
            result = EventDrivenTestResult(self.event_publisher)
        super().run(result)

    def setUp(self):
        """
        Set up the test fixture. This method is called before each test method.
        """
        if self.event_publisher:
            self.event_publisher.publish('test_setup', self._testMethodName)

    def tearDown(self):
        """
        Tear down the test fixture. This method is called after each test method.
        """
        if self.event_publisher:
            self.event_publisher.publish('test_teardown', self._testMethodName)

class EventDrivenTestLoader(unittest.TestLoader):
    """
    A TestLoader that discovers tests for event-driven execution.
    """

    def discover(self, start_dir, pattern='test*.py', top_level_dir=None):
        """
        Discover tests in the given start directory.

        :param start_dir: The directory to start discovering tests from.
        :param pattern: The pattern to match test files.
        :param top_level_dir: The top-level directory of the project.
        :return: A TestSuite containing the discovered tests.
        """
        suite = super().discover(start_dir, pattern, top_level_dir)
        return suite

