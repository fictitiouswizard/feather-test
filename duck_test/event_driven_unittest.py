import importlib
import sys
import unittest
import multiprocessing
import uuid
import time
import re
from duck_test.events import EventBus, TestMessage
from duck_test.test_servers import TestServer
from duck_test.utils import to_snake_case


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
    def __init__(self, processes=None, reporters=None, server='TestServer'):
        self.processes = processes or multiprocessing.cpu_count()
        self.manager = multiprocessing.Manager()
        self.event_queue = self.manager.Queue()
        self.event_bus = EventBus(self.event_queue)
        self.event_publisher = self.event_bus.get_publisher()
        self.test_server = self._create_test_server(server)
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

    def _create_test_server(self, server_class_name):
        return self._create_extension('server', server_class_name)

    def _create_reporter(self, reporter_class_name):
        return self._create_extension('reporter', reporter_class_name)

    def _create_extension(self, extension_type, class_name):
        # Try to load from built-in extensions first
        if extension_type == 'server':
            built_in_module = 'duck_test.test_servers'
        else:  # reporter
            built_in_module = 'duck_test.reporters'
        
        try:
            module = importlib.import_module(built_in_module)
            extension_class = getattr(module, class_name)
        except AttributeError:
            # If not found in built-in, try to import from third-party package
            try:
                module_name = f'duck_test_{extension_type}_{class_name.lower()}'
                module = importlib.import_module(module_name)
                extension_class = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                raise ValueError(f"{extension_type.capitalize()} '{class_name}' not found: {str(e)}")
        
        if extension_type == 'server':
            return extension_class(self.processes, self.event_queue)
        else:  # reporter
            return extension_class()

    def _create_test_server(self, server_name):
        if isinstance(server_name, str):
            # Try to load from __main__ first
            main_module = sys.modules['__main__']
            server_class = getattr(main_module, server_name, None)
            
            if server_class is None:
                # If not found in __main__, try duck_test.test_servers
                try:
                    snake_case_name = to_snake_case(server_name)
                    module = importlib.import_module(f'duck_test.test_servers.{snake_case_name}')
                    server_class = getattr(module, server_name)
                except (ImportError, AttributeError):
                    # If not found in duck_test.test_servers, try to import from any installed package
                    try:
                        module_name, class_name = server_name.rsplit('.', 1)
                        
                        # Check if the module name follows the duck_test_server_* convention
                        if not module_name.startswith('duck_test_server_'):
                            raise ValueError(f"Third-party test server '{module_name}' does not follow the duck_test_server_* naming convention")
                        
                        # Import directly using the module name
                        module = importlib.import_module(module_name)
                        server_class = getattr(module, class_name)
                    except (ImportError, AttributeError, ValueError) as e:
                        raise ValueError(f"Test server '{server_name}' not found or invalid: {str(e)}")
            
            return server_class(self.processes, self.event_queue)
        elif isinstance(server_name, type) and issubclass(server_name, TestServer):
            return server_name(self.processes, self.event_queue)
        else:
            raise ValueError("Server must be a string name or a TestServer subclass")

class EventDrivenTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_publisher = None
        self.correlation_id = str(uuid.uuid4())
        self.run_correlation_id = None
        self.test_name = self._testMethodName
        self.class_name = self.__class__.__name__
        self.module_name = self.__class__.__module__

    def set_event_publisher(self, publisher):
        self.event_publisher = publisher

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

