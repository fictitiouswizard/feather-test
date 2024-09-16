# Introducing Feather Test: An Event-Driven Testing Framework for Python

Hello, I've been working on a new testing framework called Feather Test. It's designed to bring event-driven architecture to Python testing, offering flexibility, parallel execution, and customizable reporting.

## Key Features

- 🚀 Event-driven architecture for flexible test execution and reporting
- ⚡ Parallel test execution for improved performance
- 📊 Customizable reporters for tailored test output
- 🧰 Command-line interface similar to unittest for ease of use
- 🎨 Support for custom events during test execution

## What My Project Does

Feather Test is a Python testing framework that introduces event-driven architecture to the testing process. It allows developers to:

1. Write tests using a familiar unittest-like syntax
2. Execute tests in parallel for improved performance
3. Create custom reporters for tailored test output
4. Extend the test execution environment with custom test servers
5. Utilize custom events during test execution for more flexible testing scenarios

## Quick Example

Here's a simple test case using Feather Test:

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

## Target Audience

Feather Test is designed for:

- Python developers looking for a more flexible and extensible testing framework
- Teams working on medium to large-scale projects that could benefit from parallel test execution
- Developers interested in event-driven architecture and its application to testing
- Anyone looking to customize their test reporting or execution environment


## Comparison

Compared to existing Python testing frameworks like unittest, pytest, or nose, Feather Test offers:

1. **Event-Driven Architecture**: Unlike traditional frameworks, Feather Test uses events for test execution and reporting, allowing for more flexible and decoupled test processes.
2. **Built-in Parallel Execution**: While other frameworks may require plugins or additional configuration, Feather Test supports parallel test execution out of the box.
3. **Customizable Reporters**: Feather Test makes it easy to create custom reporters, giving you full control over how test results are presented and stored.
4. **Extensible Test Servers**: The ability to create custom test servers allows for more advanced test setup and teardown processes, which can be particularly useful for integration or system tests.
5. **Custom Events**: Feather Test allows you to publish and subscribe to custom events during test execution, enabling more complex testing scenarios and better integration with external systems or services.

While Feather Test introduces these new concepts, it maintains a familiar API for those coming from unittest, making it easier for developers to transition and adopt.


## Custom Reporters

One of the coolest features is the ability to create custom reporters. Here's a simple example:

```python
from feather_test.reporters.base_reporter import BaseReporter

class CustomReporter(BaseReporter):
    def on_test_success(self, correlation_id, test_name, class_name, module_name):
        print(f"✅ Test passed: {module_name}.{class_name}.{test_name}")

    def on_test_failure(self, correlation_id, test_name, class_name, module_name, failure):
        print(f"❌ Test failed: {module_name}.{class_name}.{test_name}")
        print(f"   Reason: {failure}")
```

## Custom Test Servers

Feather Test also supports custom test servers for extending the test execution environment. Here's a snippet from the documentation:

```python
import types
from feather_test.test_server import TestServer

class ContextInjectorServer(TestServer):
    def __init__(self, processes, event_queue):
        super().__init__(processes, event_queue)
        self.setup_hooks()

    def setup_hooks(self):
        @self.hook_manager.register('after_import')
        def inject_context_module(context):
            # Create a new module to inject
            injected_module = types.ModuleType('feather_test_context')

            # Add utility functions
            def assert_eventually(condition, timeout=5, interval=0.1):
                import time
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if condition():
                        return True
                    time.sleep(interval)
                raise AssertionError("Condition not met within the specified timeout")

            injected_module.assert_eventually = assert_eventually

            # Add a configuration object
            class Config:
                DEBUG = True
                API_URL = "https://api.example.com"

            injected_module.config = Config()

            # Add the event publisher to the injected module
            injected_module.event_publisher = context['event_publisher']

            # Inject the module into the test module's globals
            context['module'].__dict__['feather_test_context'] = injected_module

        @self.hook_manager.register('before_create_test')
        def setup_test_attributes(context):
            # Add attributes or methods to the test class
            context['test_class'].injected_attribute = "This is an injected attribute"
```

## Why Feather Test?

1. **Flexibility**: The event-driven architecture allows for more flexible test execution and reporting.
2. **Performance**: Built-in support for parallel test execution can significantly speed up your test suite.
3. **Extensibility**: Easy to extend with custom reporters and test servers.
4. **Familiar**: If you're comfortable with unittest, you'll feel right at home with Feather Test.

## Installation

You can install Feather Test using pip:

```bash
pip install feather-test
```

## Learn More

Check out the full documentation and source code on GitHub: [Feather Test Repository](https://github.com/fictitiouswizard/feather-test)

I'd love to hear your thoughts and feedback! Feel free to ask questions, suggest improvements, or share your experience if you give it a try. Happy testing! 🐍✨
