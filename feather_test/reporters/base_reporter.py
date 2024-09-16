class BaseReporter:
    def on_test_run_start(self, correlation_id, **kwargs): pass
    def on_test_run_end(self, correlation_id, **kwargs): pass
    def on_test_start(self, correlation_id, **kwargs): pass
    def on_test_end(self, correlation_id, **kwargs): pass
    def on_test_success(self, correlation_id, **kwargs): pass
    def on_test_error(self, correlation_id, **kwargs): pass
    def on_test_failure(self, correlation_id, **kwargs): pass