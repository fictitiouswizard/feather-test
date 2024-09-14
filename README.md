# Duck Test

Duck Test is an event-driven testing framework for Python, inspired by the unittest module but with enhanced features for parallel execution and customizable reporting.

## Features

- Event-driven architecture for flexible test execution and reporting
- Parallel test execution for improved performance
- Customizable reporters for tailored test output
- Command-line interface similar to unittest for ease of use
- Support for custom events during test execution

## Installation

You can install Duck Test using pip:

```bash
pip install duck-test
```

## Usage

### Command-line Interface

Duck Test can be run from the command line, similar to unittest:

```bash
duck-test [options] [start_directory]
```

Options:
- `-v`, `--verbose`: Verbose output
- `-f`, `--failfast`: Stop on first fail or error
- `-c`, `--catch`: Catch control-C and display results
- `-b`, `--buffer`: Buffer stdout and stderr during tests
- `-k PROCESSES`, `--processes PROCESSES`: Number of processes to use
- `-r REPORTER`, `--reporter REPORTER`: Reporter to use (default: DefaultReporter)
- `-p PATTERN`, `--pattern PATTERN`: Pattern to match test files (default: test*.py)

You can also pass reporter-specific arguments by prefixing them with the reporter name:

```bash
duck-test -r CustomReporter --customreporter-output-file report.txt --customreporter-verbose
```

### Writing Tests

Tests are written similarly to unittest, but inherit from \`EventDrivenTestCase\`:

```python
from duck_test import EventDrivenTestCase

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
from duck_test.event_driven_unittest import BaseReporter

class CustomReporter(BaseReporter):
    def __init__(self, output_file=None, verbose=False):
        self.output_file = output_file
        self.verbose = verbose
        self.total_tests = 0
        self.passed_tests = 0

    def on_test_run_start(self, correlation_id, **kwargs):
        print(f"Test run started (Run ID: {kwargs['run_id']}")

    def on_test_success(self, correlation_id, **kwargs):
        self.passed_tests += 1
        if self.verbose:
            print(f"Test passed: {kwargs['module_name']}.{kwargs['class_name']}.{kwargs['test_name']}")

    def on_test_run_end(self, correlation_id, **kwargs):
        print(f"Tests completed. Passed: {self.passed_tests}/{self.total_tests}")
        if self.output_file:
            with open(self.output_file, 'w') as f:
                f.write(f"Passed: {self.passed_tests}/{self.total_tests}")
```

### Programmatic Usage

You can also use Duck Test programmatically:

```python
from duck_test import EventDrivenTestRunner
import unittest

def run_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MyTest))

    runner = EventDrivenTestRunner(processes=2, verbosity=2, reporters=['CustomReporter'])
    runner.run(suite)

if __name__ == '__main__':
    run_tests()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.