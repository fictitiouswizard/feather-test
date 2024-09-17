import multiprocessing
from multiprocessing import Pool
from functools import wraps
from feather_test.events import TestMessage, EventPublisher
from feather_test.event_driven_test_result import EventDrivenTestResult
import sys
import traceback
from unittest import TestCase
import uuid
import logging

logger = logging.getLogger("feather_test")

class LoadFailedTestCase(TestCase):
    """A custom TestCase to represent a test that failed to load."""

    def __init__(self, test_name, exception):
        super().__init__('run')
        self.test_name = test_name
        self.exception = exception
        self.class_name = self.__class__.__name__
        self.module_name = self.__class__.__module__
        self.correlation_id = str(uuid.uuid4())  # Generate a correlation_id here

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()
        result.startTest(self)
        result.addError(self, (type(self.exception), self.exception, None))
        result.stopTest(self)

class HookManager:
    """
    HookManager is responsible for managing and executing hooks at various points
    during the test execution process.

    Hooks are user-defined functions that can be registered to run at specific points
    in the test lifecycle, allowing for customization and extension of the test execution process.

    Attributes:
        hooks (dict): A dictionary containing lists of hook functions for each hook point.
    """

    def __init__(self):
        """
        Initialize the HookManager with empty lists for each hook point.
        """
        self.hooks = {
            'before_import': [],
            'after_import': [],
            'before_get_test_class': [],
            'after_get_test_class': [],
            'before_create_test': [],
            'after_create_test': [],
            'before_run_test': [],
            'after_run_test': [],
        }

    def register(self, hook_name):
        """
        Decorator for registering a function as a hook.

        :param hook_name: The name of the hook point to register the function for.
        :return: A decorator function.
        :raises ValueError: If an unknown hook name is provided.
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            if hook_name not in self.hooks:
                raise ValueError(f"Unknown hook: {hook_name}")
            self.hooks[hook_name].append(wrapper)
            return wrapper
        return decorator

    def run_hooks(self, hook_name, context):
        """
        Execute all registered hooks for a given hook point.

        :param hook_name: The name of the hook point to execute.
        :param context: A dictionary containing context information for the hook execution.
        :raises ValueError: If an unknown hook name is provided.
        """
        if hook_name not in self.hooks:
            raise ValueError(f"Unknown hook: {hook_name}")
        for hook in self.hooks[hook_name]:
            try:
                hook(context)
            except Exception as e:
                print(f"Error in {hook_name} hook: {str(e)}")

class TestServer:
    """
    TestServer is responsible for managing the execution of tests in parallel processes.

    It handles the distribution of tests to worker processes, manages the test queue,
    and coordinates the execution of hooks throughout the test lifecycle.

    Attributes:
        processes (int): The number of worker processes to use for test execution.
        event_queue (multiprocessing.Queue): A queue for publishing test events.
        test_queue (multiprocessing.Queue): A queue for distributing tests to worker processes.
        hook_manager (HookManager): An instance of HookManager for managing test lifecycle hooks.
    """

    def __init__(self, processes, event_publisher):
        """
        Initialize the TestServer.

        :param processes: The number of worker processes to use.
        :param event_queue: A multiprocessing Queue for publishing test events.
        """
        self.processes = processes
        self.event_publisher = event_publisher
        self.test_queue = multiprocessing.Manager().Queue()
        self.hook_manager = HookManager()

    def start(self):
        """
        Start the test server and begin processing tests.

        This method creates a pool of worker processes and distributes tests to them.
        """
        with Pool(processes=self.processes) as pool:
            pool.map(self._run_test_process, range(self.processes))

    def add_test(self, test_message):
        """
        Add a test to the test queue for execution.

        :param test_message: A TestMessage object representing the test to be executed.
        """
        self.test_queue.put(test_message.to_json())

    def _run_test_process(self, process_id):
        """
        The main loop for a worker process, continuously processing tests from the queue.

        :param process_id: An identifier for the worker process.
        """
        while True:
            try:
                test_json = self.test_queue.get(block=False)
                test_message = TestMessage.from_json(test_json)
                self._run_single_test(test_message, self.event_publisher)
            except multiprocessing.queues.Empty:
                break

    def _run_single_test(self, test_message, event_publisher):
        """
        Execute a single test, including all associated hooks.

        :param test_message: A TestMessage object representing the test to be executed.
        :param event_publisher: An EventPublisher for publishing test events.
        """
        context = {
            'test_message': test_message,
            'event_publisher': event_publisher,
            'module': None,
            'test_class': None,
            'test_instance': None
        }

        try:
            self.hook_manager.run_hooks('before_import', context)
            context['module'] = self._import_test_module(test_message)
            self.hook_manager.run_hooks('after_import', context)

            self.hook_manager.run_hooks('before_get_test_class', context)
            context['test_class'] = getattr(context['module'], test_message.class_name)
            self.hook_manager.run_hooks('after_get_test_class', context)

            self.hook_manager.run_hooks('before_create_test', context)
            try:
                context['test_instance'] = context['test_class'](test_message.test_name)
            except Exception as e:
                # Handle the case where the test failed to load
                error_message = f"Failed to load test: {test_message.test_name}. Error: {str(e)}"
                context['test_instance'] = LoadFailedTestCase(test_message.test_name, Exception(error_message))
            
            if hasattr(context['test_instance'], 'set_event_publisher'):
                context['test_instance'].set_event_publisher(event_publisher)
            self.hook_manager.run_hooks('after_create_test', context)

            self.hook_manager.run_hooks('before_run_test', context)
            self._run_test(context['test_instance'], event_publisher)
            self.hook_manager.run_hooks('after_run_test', context)
        except Exception as e:
            error_type, error_value, error_traceback = sys.exc_info()
            formatted_traceback = ''.join(traceback.format_exception(error_type, error_value, error_traceback))
            event_publisher.publish('test_error', context['test_instance'].correlation_id,
                                    test_name=test_message.test_name,
                                    class_name=test_message.class_name,
                                    module_name=test_message.module_name,
                                    error=f"{str(e)}\n{formatted_traceback}")

    def _import_test_module(self, test_message):
        """
        Import the module containing the test to be executed.

        :param test_message: A TestMessage object containing the module name.
        :return: The imported module.
        """
        return __import__(test_message.module_name, fromlist=[test_message.class_name])

    def _run_test(self, test, event_publisher):
        """
        Execute a single test instance.

        :param test: An instance of a test class to be executed.
        :param event_publisher: An EventPublisher for publishing test events.
        """
        result = EventDrivenTestResult(event_publisher)
        test.run(result)
