# Feather Test

Feather Test is an event-driven testing framework for Python, inspired by the unittest module but with enhanced features for parallel execution and customizable reporting.

## Features

- Event-driven architecture for flexible test execution and reporting
- Parallel test execution for improved performance
- Customizable reporters for tailored test output
- Command-line interface similar to unittest for ease of use
- Support for custom events during test execution

## Installation

You can install Feather Test using pip:

```bash
pip install feather-test
```

## Usage

### Command-line Interface

Feather Test can be run from the command line, similar to unittest:

```bash
feather [options] [start_directory]
```

Options:
- `-f`, `--failfast`: Stop on first fail or error
- `-c`, `--catch`: Catch control-C and display results
- `-k PROCESSES`, `--processes PROCESSES`: Number of processes to use
- `-r REPORTER`, `--reporter REPORTER`: Reporter to use (default: DefaultReporter)
- `-p PATTERN`, `--pattern PATTERN`: Pattern to match test files (default: test*.py)

You can also pass reporter-specific arguments by prefixing them with the reporter name:

```bash
feather -r CustomReporter --customreporter-output-file report.txt --customreporter-verbose
```

### Writing Tests

Tests are written similarly to unittest, but inherit from \`EventDrivenTestCase\`:

```python
from feather_test import EventDrivenTestCase

class MyTest(EventDrivenTestCase):
    def test_example(self):
        self.assertTrue(True)

    def test_custom_event(self):
        self.event_publisher.publish('custom_event', self.correlation_id, 
                                     data='Custom event data')
        self.assertEqual(1, 1)
```

### Custom Reporters

You can create custom reporters by inheriting from \`BaseReporter\`:

```python
from feather_test.event_driven_unittest import BaseReporter

class CustomReporter(BaseReporter):
    def __init__(self, output_file=None, verbose=False):
        self.output_file = output_file
        self.verbose = verbose
        self.total_tests = 0
        self.passed_tests = 0

    def on_test_run_start(self, correlation_id, run_id):
        print(f"Test run started (Run ID: {run_id}")

    def on_test_success(self, correlation_id, test_name, class_name, module_name):
        self.passed_tests += 1
        if self.verbose:
            print(f"Test passed: {module_name}.{class_name}.{test_name}")

    def on_test_run_end(self, correlation_id, run_id):
        print(f"Tests completed. Passed: {self.passed_tests}/{self.total_tests}")
        if self.output_file:
            with open(self.output_file, 'w') as f:
                f.write(f"Passed: {self.passed_tests}/{self.total_tests}")
```

### Programmatic Usage

You can also use Feather Test programmatically:

```python
from feather_test import EventDrivenTestRunner
import unittest

def run_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MyTest))

    runner = EventDrivenTestRunner(processes=2, verbosity=2, reporters=['CustomReporter'])
    runner.run(suite)

if __name__ == '__main__':
    run_tests()
```

## Events

Feather Test emits various events during the test execution process. Custom reporters can listen for these events to provide detailed and customized test reports. Here's a list of all events that can be emitted:

1. `test_run_start`: Emitted when the entire test run begins.
   - Data: `run_id`

2. `test_run_end`: Emitted when the entire test run completes.
   - Data: `run_id`

3. `test_start`: Emitted when an individual test method starts.
   - Data: `test_name`, `class_name`, `module_name`

4. `test_end`: Emitted when an individual test method ends.
   - Data: `test_name`, `class_name`, `module_name`

5. `test_success`: Emitted when a test passes successfully.
   - Data: `test_name`, `class_name`, `module_name`

6. `test_failure`: Emitted when a test fails.
   - Data: `test_name`, `class_name`, `module_name`, `failure` (error message and traceback)

7. `test_error`: Emitted when a test raises an unexpected exception.
   - Data: `test_name`, `class_name`, `module_name`, `error` (error message and traceback)

8. `test_skip`: Emitted when a test is skipped.
   - Data: `test_name`, `class_name`, `module_name`, `reason`

9. `test_setup`: Emitted when the setUp method of a test case is called.
   - Data: `test_name`

10. `test_teardown`: Emitted when the tearDown method of a test case is called.
    - Data: `test_name`

11. `test_run_error`: Emitted if there's an error in the test running process itself.
    - Data: `error` (error message and traceback)

Custom events can also be emitted from within tests using the `self.event_publisher.publish()` method. These events will be passed to reporters with whatever data is provided.

When creating custom reporters, you can define methods to handle these events. The method names should be in the format `on_<event_name>`. For example, to handle the `test_start` event, you would define an `on_test_start` method in your reporter class.

### Emitting Custom Events

You can emit custom events from within your tests using the `event_publisher`:

```python
class MyTest(EventDrivenTestCase):
    def test_example(self):
        self.event_publisher.publish('my_custom_event', self.correlation_id,
                                     custom_data='Some interesting information')
        self.assertTrue(True)
```

Custom reporters can then handle these events by defining an `on_my_custom_event` method.

# Third-Party Extensions for Feather Test

Feather Test supports third-party TestServers and Reporters, allowing the community to extend the framework's functionality.

## Naming Convention

All third-party packages for Feather Test must follow this specific naming convention:

- For TestServers:
  - Package name: `feather-test-server-<name>`
  - Python module name: `feather_test_server_<name>`
  - Main class name: `<Name>TestServer`

- For Reporters:
  - Package name: `feather-test-reporter-<name>`
  - Python module name: `feather_test_reporter_<name>`
  - Main class name: `<Name>Reporter`

This convention helps maintain consistency, avoid naming conflicts, and makes the purpose of each package immediately clear.

## Creating a Third-Party TestServer Package

1. Create a new Python package named `feather-test-server-<name>` (e.g., `feather-test-server-custom`).
2. Name your Python module `feather_test_server_<name>` (e.g., `feather_test_server_custom`).
3. Implement your main TestServer class as `<Name>TestServer` (e.g., `CustomTestServer`) by subclassing `feather_test.test_server.TestServer`.
4. Publish your package to PyPI.

Example structure:

```
feather-test-server-custom/
    feather_test_server_custom/
        __init__.py
        custom_test_server.py
    setup.py
    README.md
    LICENSE
```
## Creating a Third-Party Reporter Package

1. Create a new Python package named `feather-test-reporter-<name>` (e.g., `feather-test-reporter-custom`).
2. Name your Python module `feather_test_reporter_<name>` (e.g., `feather_test_reporter_custom`).
3. Implement your main Reporter class as `<Name>Reporter` (e.g., `CustomReporter`) by subclassing `feather_test.reporters.base_reporter.BaseReporter`.
4. Publish your package to PyPI.

Example structure:

```
feather-test-reporter-custom/
    feather_test_reporter_custom/
        __init__.py
        custom_reporter.py
    setup.py
    README.md
    LICENSE
```

## Using Third-Party Extensions

After installing third-party packages, you can use them as follows:

1. Command line:
   ```
   feather -s CustomTestServer -r CustomReporter
   ```

2. Programmatically:
   ```python
   from feather_test import EventDrivenTestRunner
   
   runner = EventDrivenTestRunner(processes=2, reporters=['CustomReporter'], server='CustomTestServer')
   runner.discover_and_run('tests')
   ```

Note: When using third-party extensions, you only need to specify the class name. The framework will automatically determine the correct module to import based on the naming convention.

For more details on creating custom TestServers and Reporters, refer to the respective documentation sections.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.