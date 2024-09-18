import importlib
import sys
import unittest
import multiprocessing
import uuid
import time
from feather_test.events import EventBus, TestMessage
from feather_test.test_servers import TestServer
from feather_test.utils import to_snake_case
import logging

logger = logging.getLogger("feather_test")


class EventDrivenTestRunner:
    """
    A test runner that discovers and executes tests, publishing events throughout the process.

    This runner integrates with the event-driven architecture of Feather Test,
    allowing for parallel test execution and custom reporting.

    Attributes:
        processes (int): Number of processes to use for parallel test execution.
        manager (multiprocessing.Manager): A manager for sharing objects between processes.
        event_queue (multiprocessing.Queue): A queue for sharing events between processes.
        event_bus (EventBus): An instance of EventBus for managing events.
        event_publisher (EventPublisher): An instance of EventPublisher for sending events.
        test_server (TestServer): An instance of TestServer for managing test execution.
        test_loader (unittest.TestLoader): A loader for discovering tests.
        run_correlation_id (str): A unique identifier for the test run.
    """

    def __init__(self, processes=None, reporters=None, server='TestServer', **kwargs):
        """
        Initialize the EventDrivenTestRunner.

        :param processes: Number of processes to use for parallel test execution.
        :param reporters: List of reporter names to use for test reporting.
        :param server: Name of the TestServer class to use.
        """
        self.processes = processes or multiprocessing.cpu_count()
        self.manager = multiprocessing.Manager()
        self.event_queue = self.manager.Queue() 
        self.event_bus = EventBus(self.event_queue)

        # self.event_publisher = self.event_bus.get_publisher()
        self.test_server = self._create_test_server(server)
        self.test_loader = unittest.TestLoader()
        self.run_correlation_id = str(uuid.uuid4())

        if reporters:
            for reporter in reporters:
                self.event_bus.load_reporter(reporter)

    def discover_and_run(self, start_dir, pattern='test*.py', top_level_dir=None):
        """
        Discover and run tests in the specified directory.

        :param start_dir: Directory to start discovering tests.
        :param pattern: Pattern to match test files.
        :param top_level_dir: Top level directory of the project.
        :return: TestResult containing the results of the test run.
        """
        suite = self.test_loader.discover(start_dir, pattern, top_level_dir)
        return self.run(suite)

    def run(self, test_suite):
        """
        Run the given test suite.

        :param test_suite: A TestSuite object containing tests to run.
        :return: TestResult containing the results of the test run.
        """
        self._enqueue_tests(test_suite)
        self.event_bus.start()
        self.event_bus.event_publisher.publish('test_run_start', self.run_correlation_id, run_id=self.run_correlation_id)

        self.test_server.start()
        
        self.event_bus.event_publisher.publish('test_run_end', self.run_correlation_id, run_id=self.run_correlation_id)

        self._process_remaining_events()
        self._stop_reporters()

    def _enqueue_tests(self, suite):
        """
        Recursively enqueue tests from a test suite.

        :param suite: A TestSuite object or a single test case.
        """
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
        """
        Process any remaining events in the queue and stop the event processor.
        """
        if not self.event_bus.event_queue.empty():
            logger.warning(f"There are {self.event_bus.event_queue.unfinished_tasks} events left in the queue")
        # Wait for a short time to allow remaining events to be processed
        time.sleep(0.5)
        # self.event_bus.publish('STOP', None)
        # self.event_processor.join(timeout=5)
        # if self.event_processor.is_alive():
        #     self.event_processor.terminate()

    def _create_test_server(self, server_name):
        """
        Create and return an instance of the specified TestServer.

        :param server_name: Name of the TestServer class to instantiate.
        :return: An instance of the specified TestServer.
        :raises ValueError: If the specified TestServer cannot be found or instantiated.
        """
        if isinstance(server_name, str):
            # Try to load from __main__ first
            main_module = sys.modules['__main__']
            server_class = getattr(main_module, server_name, None)
            
            if server_class is None:
                # If not found in __main__, try feather_test.test_servers
                try:
                    snake_case_name = to_snake_case(server_name)
                    module = importlib.import_module(f'feather_test.test_servers.{snake_case_name}')
                    server_class = getattr(module, server_name)
                except (ImportError, AttributeError):
                    # If not found in feather_test.test_servers, try to import from any installed package
                    try:
                        module_name, class_name = server_name.rsplit('.', 1)
                        
                        # Check if the module name follows the feather_test_server_* convention
                        if not module_name.startswith('feather_test_server_'):
                            raise ValueError(f"Third-party test server '{module_name}' does not follow the feather_test_server_* naming convention")
                        
                        # Import directly using the module name
                        module = importlib.import_module(module_name)
                        server_class = getattr(module, class_name)
                    except (ImportError, AttributeError, ValueError) as e:
                        raise ValueError(f"Test server '{server_name}' not found or invalid: {str(e)}")
            
            return server_class(self.processes, self.event_bus.event_publisher)
        elif isinstance(server_name, type) and issubclass(server_name, TestServer):
            return server_name(self.processes, self.event_bus.event_publisher)
        else:
            raise ValueError("Server must be a string name or a TestServer subclass")

    def _stop_reporters(self):
        """
        Stop all reporters.
        """
        self.event_bus.stop()
        # for reporter in self.event_bus.reporters:
            # reporter.stop()


class EventDrivenTestCase(unittest.TestCase):
    """
    A TestCase class that integrates with the event-driven architecture of Feather Test.

    This class extends unittest.TestCase to add event publishing capabilities and
    additional metadata for each test case.

    Attributes:
        event_publisher (EventPublisher): An instance of EventPublisher for sending events.
        correlation_id (str): A unique identifier for the test case.
        run_correlation_id (str): A unique identifier for the test run.
        test_name (str): The name of the test method.
        class_name (str): The name of the test class.
        module_name (str): The name of the module containing the test.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the EventDrivenTestCase.

        :param args: Positional arguments to pass to unittest.TestCase.
        :param kwargs: Keyword arguments to pass to unittest.TestCase.
        """
        super().__init__(*args, **kwargs)
        self.event_publisher = None
        self.correlation_id = str(uuid.uuid4())
        self.run_correlation_id = None
        self.test_name = self._testMethodName
        self.class_name = self.__class__.__name__
        self.module_name = self.__class__.__module__

    def set_event_publisher(self, publisher):
        """
        Set the event publisher for this test case.

        :param publisher: An instance of EventPublisher.
        """
        self.event_publisher = publisher

    def run(self, result=None):
        """
        Run the test, using EventDrivenTestResult if no result is provided.

        :param result: A TestResult object to store the results of the test.
        :return: The TestResult object after running the test.
        """
        if result is None:
            result = self.defaultTestResult()
        result.startTest(self)
        testMethod = getattr(self, self._testMethodName)
        try:
            success = False
            try:
                self.setUp()
            except Exception:
                result.addError(self, sys.exc_info())
                return
            try:
                testMethod()
            except unittest.SkipTest as e:
                result.addSkip(self, str(e))
            except Exception:
                result.addFailure(self, sys.exc_info())
            else:
                success = True
            try:
                self.tearDown()
            except Exception:
                success = False
                result.addError(self, sys.exc_info())
            if success:
                result.addSuccess(self)
        finally:
            result.stopTest(self)
        return result

    def setUp(self):
        """
        Set up the test fixture. This method is called before each test method.

        Publishes a 'test_setup' event if an event publisher is available.
        """
        if self.event_publisher:
            self.event_publisher.publish('test_setup', self.correlation_id, test_name=self._testMethodName)

    def tearDown(self):
        """
        Tear down the test fixture. This method is called after each test method.

        Publishes a 'test_teardown' event if an event publisher is available.
        """
        if self.event_publisher:
            self.event_publisher.publish('test_teardown', self.correlation_id, test_name=self._testMethodName)

