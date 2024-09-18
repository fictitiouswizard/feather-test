import json
import traceback
from typing import Dict
from feather_test.utils.reporter_loader import load_reporter
import multiprocessing
import sys
import os
import traceback
import logging
from typing import Dict
import threading

logger = logging.getLogger("feather_test")

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

class ReporterProcess:
    def __init__(self, reporter_class_or_instance, *args, **kwargs):
        self.reporter_class_or_instance = reporter_class_or_instance
        self.args = args
        self.kwargs = kwargs
        self.event_queue = multiprocessing.Queue()
        self.stdout_queue = multiprocessing.Queue()
        self.process = None
        logger.debug(f"ReporterProcess initialized for {reporter_class_or_instance}")

    def start(self):
        self.process = multiprocessing.Process(target=self._run)
        self.process.start()
        logger.debug(f"ReporterProcess started with PID {self.process.pid}")

    def _run(self):
        try:
            sys.stdout = StdoutRedirector(self.stdout_queue)
            sys.stderr = sys.stdout

            if callable(self.reporter_class_or_instance):
                reporter = self.reporter_class_or_instance(*self.args, **self.kwargs)
            else:
                reporter = self.reporter_class_or_instance

            logger.debug(f"Reporter {reporter.__class__.__name__} initialized in process {os.getpid()}")

            while True:
                try:
                    event = self.event_queue.get(timeout=1)
                    if event is None:
                        break
                    event_type, correlation_id, kwargs = event
                    logger.debug(f"Received event: {event_type}, {correlation_id}")
                    method_name = f"on_{event_type}"
                    if hasattr(reporter, method_name):
                        getattr(reporter, method_name)(correlation_id=correlation_id, **kwargs)
                    else:
                        logger.warning(f"Reporter {reporter.__class__.__name__} has no method {event_type}")
                except multiprocessing.queues.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error in reporter process: {e}")
                    logger.error(traceback.format_exc())

            logger.debug(f"Reporter process {os.getpid()} stopping")
        except Exception as e:
            logger.error(f"Error initializing reporter: {e}")
            logger.error(traceback.format_exc())
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

    def send_event(self, event_type, correlation_id, **kwargs):
        if self.process and self.process.is_alive():
            try:
                self.event_queue.put((event_type, correlation_id, kwargs))
                logger.debug(f"Sent event to reporter: {event_type}, {correlation_id}")
            except BrokenPipeError:
                logger.error(f"BrokenPipeError: Reporter process may have terminated unexpectedly")
        else:
            logger.warning(f"Attempted to send event to terminated reporter process")

    def stop(self):
        if self.process and self.process.is_alive():
            try:
                self.event_queue.put(None)
                self.process.join(timeout=5)
                if self.process.is_alive():
                    logger.warning(f"Reporter process did not terminate gracefully, forcing termination")
                    self.process.terminate()
            except Exception as e:
                logger.error(f"Error stopping reporter process: {e}")

class StdoutRedirector:
    def __init__(self, queue):
        self.queue = queue

    def write(self, msg):
        self.queue.put(msg)

    def flush(self):
        sys.__stdout__.flush()

class EventBus:
    def __init__(self, event_queue):
        self.reporters: Dict[str, ReporterProcess] = {}
        self.event_queue = event_queue
        self.event_publisher = EventPublisher(self.event_queue)
        self.is_running = False
        self.thread = None
        logger.debug("EventBus initialized")

    def load_reporter(self, reporter_name, *args, **kwargs):
        reporter_class_or_instance = load_reporter(reporter_name)
        if reporter_class_or_instance:
            reporter_process = ReporterProcess(reporter_class_or_instance, *args, **kwargs)
            self.reporters[reporter_name] = reporter_process
            reporter_process.start()
            logger.debug(f"Reporter loaded and started: {reporter_name}")
        else:
            logger.error(f"Failed to load reporter: {reporter_name}")

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        logger.debug("EventBus thread started")

    def _run(self):
        logger.debug("EventBus _run method started")
        while self.is_running:
            try:
                for reporter_name, reporter in self.reporters.items():
                    while not reporter.stdout_queue.empty():
                        stdout_msg = reporter.stdout_queue.get_nowait()
                        sys.stdout.write(stdout_msg)
                        sys.stdout.flush()
                        logger.debug(f"Stdout from {reporter_name}: {stdout_msg.strip()}")

                try:
                    event = self.event_queue.get(timeout=0.1)
                    event_type, correlation_id, kwargs = event
                    logger.debug(f"Processing event: {event_type}, {correlation_id}")
                    for reporter in self.reporters.values():
                        logger.debug(f"Sending event to reporter: {event_type}, {correlation_id}")
                        reporter.send_event(event_type, correlation_id, **kwargs)
                except multiprocessing.queues.Empty:
                    pass
            except Exception as e:
                logger.error(f"Error in EventBus: {e}")
                logger.error(traceback.format_exc())

    def stop(self):
        for reporter_name, reporter in self.reporters.items():
            logger.debug(f"Stopping reporter: {reporter_name}")
            reporter.stop()
        logger.debug("Stopping EventBus")
        self.is_running = False
        if self.thread:
            self.thread.join()

        logger.debug("EventBus stopped")

    def get_event_publisher(self):
        return self.event_publisher

class EventPublisher:
    def __init__(self, queue):
        self.queue = queue

    def publish(self, event_type: str, correlation_id: str, **kwargs):
        self.queue.put((event_type, correlation_id, kwargs))
        logger.debug(f"Published event: {event_type}, {correlation_id}")

