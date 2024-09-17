import unittest
import logging

logger = logging.getLogger("feather_test")


class EventDrivenTestResult(unittest.TestResult):
    """
    A custom TestResult class that publishes events for various test outcomes.

    This class extends unittest.TestResult to integrate with the event-driven
    architecture of Feather Test. It publishes events for test starts, ends,
    successes, errors, failures, skips, and unexpected successes.

    Attributes:
        event_publisher (EventPublisher): An instance of EventPublisher for sending events.
    """

    def __init__(self, event_publisher):
        """
        Initialize the EventDrivenTestResult.

        :param event_publisher: An instance of EventPublisher for sending events.
        """
        super().__init__()
        self.event_publisher = event_publisher

    def startTest(self, test):
        """
        Called when a test begins.

        :param test: The test case being run.
        """
        super().startTest(test)
        self.event_publisher.publish('test_start', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name)

    def stopTest(self, test):
        """
        Called when a test completes.

        :param test: The test case that has completed.
        """
        super().stopTest(test)
        self.event_publisher.publish('test_end', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name)

    def addSuccess(self, test):
        """
        Called when a test passes successfully.

        :param test: The test case that passed.
        """
        super().addSuccess(test)
        self.event_publisher.publish('test_success', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name)

    def addError(self, test, err):
        """
        Called when a test raises an unexpected exception.

        :param test: The test case that raised an exception.
        :param err: A tuple of values as returned by sys.exc_info().
        """
        super().addError(test, err)
        self.event_publisher.publish('test_error', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name,
                                     error=str(err))

    def addFailure(self, test, err):
        """
        Called when a test fails.

        :param test: The test case that failed.
        :param err: A tuple of values as returned by sys.exc_info().
        """
        super().addFailure(test, err)
        self.event_publisher.publish('test_failure', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name,
                                     failure=str(err))

    def addSkip(self, test, reason):
        """
        Called when a test is skipped.

        :param test: The test case that was skipped.
        :param reason: The reason for skipping the test.
        """
        super().addSkip(test, reason)
        self.event_publisher.publish('test_skip', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name,
                                     reason=reason)

    def addExpectedFailure(self, test, err):
        """
        Called when a test fails, but was expected to fail.

        :param test: The test case that failed as expected.
        :param err: A tuple of values as returned by sys.exc_info().
        """
        super().addExpectedFailure(test, err)
        self.event_publisher.publish('test_expected_failure', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name,
                                     error=str(err))

    def addUnexpectedSuccess(self, test):
        """
        Called when a test passes, but was expected to fail.

        :param test: The test case that unexpectedly passed.
        """
        super().addUnexpectedSuccess(test)
        self.event_publisher.publish('test_unexpected_success', test.correlation_id, 
                                     test_name=test.test_name,
                                     class_name=test.class_name,
                                     module_name=test.module_name)

