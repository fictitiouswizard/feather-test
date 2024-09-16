import json
import os
from datetime import datetime
from feather_test.reporters.base_reporter import BaseReporter

class JSONReporter(BaseReporter):
    def __init__(self, output_dir='test_reports', filename=None):
        print(output_dir)
        if not isinstance(output_dir, (str, bytes, os.PathLike)):
            raise TypeError("output_dir must be a string or path-like object")
        self.output_dir = str(output_dir)  # Convert to string to be safe
        self.filename = filename or f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.events = []

        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def _record_event(self, event_type, correlation_id, **kwargs):
        event = {
            'event_type': event_type,
            'correlation_id': correlation_id,
            'timestamp': datetime.now().isoformat(),
            'data': kwargs
        }
        self.events.append(event)

    def on_test_run_start(self, correlation_id, run_id):
        self._record_event('test_run_start', correlation_id, run_id=run_id)
    
    def on_test_run_error(self, correlation_id, error):
        self._record_event('test_run_error', correlation_id, error=error)

    def on_test_run_end(self, correlation_id, run_id):
        self._record_event('test_run_end', correlation_id, run_id=run_id)
        self._write_report()

    def on_test_start(self, correlation_id, test_name, class_name, module_name):
        self._record_event('test_start', correlation_id, test_name=test_name, class_name=class_name, module_name=module_name)

    def on_test_success(self, correlation_id, test_name, class_name, module_name):
        self._record_event('test_success', correlation_id, test_name=test_name, class_name=class_name, module_name=module_name)

    def on_test_failure(self, correlation_id, test_name, class_name, module_name, failure):
        self._record_event('test_failure', correlation_id, test_name=test_name, class_name=class_name, module_name=module_name, failure=failure)

    def on_test_error(self, correlation_id, test_name, class_name, module_name, error):
        self._record_event('test_error', correlation_id, test_name=test_name, class_name=class_name, module_name=module_name, error=error)

    def on_test_skip(self, correlation_id, test_name, class_name, module_name, reason):
        self._record_event('test_skip', correlation_id, test_name=test_name, class_name=class_name, module_name=module_name, reason=reason)

    def _write_report(self):
        file_path = os.path.join(self.output_dir, self.filename)
        with open(file_path, 'w') as f:
            json.dump(self.events, f, indent=2)
        print(f"Test run report written to {file_path}")
