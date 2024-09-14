# Duck-Test: Event-Driven Unit Testing for Python

Duck-Test is an advanced unit testing package for Python that extends the standard `unittest` module with event-driven capabilities and parallel test execution.

## Features

- Event-driven test execution
- Real-time event publishing during test runs
- Parallel test execution using multiple processes
- Seamless integration with existing unittest-based tests
- Customizable event subscriptions for detailed test monitoring

## Installation

You can install Duck-Test using pip:

```bash
pip install duck-test
```

## Quick Start

Here's a simple example of how to use Mallard:

```python
from duck_test.unittest import EventBus, EventDrivenTestCase, EventDrivenTestRunner

# Define your test cases
class MyTest(EventDrivenTestCase):
    def test_addition(self):
        self.assertEqual(1 + 1, 2)
    def test_subtraction(self):
        self.assertEqual(3 - 1, 2)

# Set up the event bus and subscribe to events
event_bus = EventBus()

def on_test_start(test_name):
    print(f"Test started: {test_name}")

def on_test_success(test_name):
    print(f"Test succeeded: {test_name}")

event_bus.subscribe('test_start', on_test_start)
event_bus.subscribe('test_success', on_test_success)

suite = unittest.TestSuite()
suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ExampleTest1))
suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ExampleTest2))

# Create the test runner and run tests
runner = EventDrivenTestRunner(event_bus)
result = runner.run(suite)
```

## Available Events

Duck-Test publishes the following events during test execution:

- `test_start`: Fired when a test method starts
- `test_end`: Fired when a test method ends
- `test_success`: Fired when a test passes
- `test_error`: Fired when a test raises an error
- `test_failure`: Fired when a test fails
- `test_setup`: Fired when test setup begins
- `test_teardown`: Fired when test teardown begins
- `test_run_start`: Fired when the entire test run starts
- `test_run_end`: Fired when the entire test run ends

You can subscribe to these events using the `EventBus.subscribe()` method.

## Advanced Usage

### Parallel Test Execution

Duck-Test supports parallel test execution using multiple processes:

```python
from duck_test.unittest import EventDrivenTestRunner

# Create the test runner with parallel execution
runner = EventDrivenTestRunner(event_bus, num_processes=4)
result = runner.discover_and_run('tests')
```

### Custom Event Handling

You can subscribe to various events to customize test monitoring and reporting:

```python
event_bus.subscribe('test_failure', lambda data: print(f"Test failed: {data[0]}"))
event_bus.subscribe('test_error', lambda data: print(f"Test error: {data[0]}"))
```

## Contributing

We welcome contributions to Duck-Test! If you have suggestions or improvements, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.