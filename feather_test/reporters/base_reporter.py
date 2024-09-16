class BaseReporter:
    """
    BaseReporter is an abstract base class for creating custom reporters in Feather Test.
    
    This class defines a set of methods that are called at various points during the test execution process.
    Subclasses should override these methods to implement custom reporting behavior.

    All methods receive a `correlation_id` parameter, which is a unique identifier for each test run,
    allowing for tracking and grouping of related events.

    Additional keyword arguments (`**kwargs`) are provided to each method for future extensibility.
    Additional arguements must be defined in the method signature for them to be passed to the reporter.
    It's important to note that these kwargs are not guaranteed to be populated and should not
    be relied upon unless explicitly documented for specific reporter implementations.
    """

    def on_test_run_start(self, correlation_id, **kwargs):
        """
        Called when a test run begins.

        :param correlation_id: Unique identifier for the test run
        :param kwargs: Additional keyword arguments (not guaranteed to be populated)
        """
        pass

    def on_test_run_end(self, correlation_id, **kwargs):
        """
        Called when a test run completes.

        :param correlation_id: Unique identifier for the test run
        :param kwargs: Additional keyword arguments (not guaranteed to be populated)
        """
        pass

    def on_test_start(self, correlation_id, **kwargs):
        """
        Called when an individual test starts.

        :param correlation_id: Unique identifier for the test run
        :param kwargs: Additional keyword arguments (not guaranteed to be populated)
        """
        pass

    def on_test_end(self, correlation_id, **kwargs):
        """
        Called when an individual test ends.

        :param correlation_id: Unique identifier for the test run
        :param kwargs: Additional keyword arguments (not guaranteed to be populated)
        """
        pass

    def on_test_success(self, correlation_id, **kwargs):
        """
        Called when a test passes successfully.

        :param correlation_id: Unique identifier for the test run
        :param kwargs: Additional keyword arguments (not guaranteed to be populated)
        """
        pass

    def on_test_error(self, correlation_id, **kwargs):
        """
        Called when a test encounters an error during execution.

        :param correlation_id: Unique identifier for the test run
        :param kwargs: Additional keyword arguments (not guaranteed to be populated)
        """
        pass

    def on_test_failure(self, correlation_id, **kwargs):
        """
        Called when a test fails.

        :param correlation_id: Unique identifier for the test run
        :param kwargs: Additional keyword arguments (not guaranteed to be populated)
        """
        pass