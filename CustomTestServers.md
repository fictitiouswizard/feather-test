# Custom Test Servers in Duck Test

Duck Test allows you to create custom test servers to extend and customize the test execution environment. This guide will walk you through creating a custom test server that injects a context module into your tests.

## Creating a Custom Test Server

To create a custom test server, follow these steps:

1. Create a new Python file in the `duck_test/test_servers/` directory.
2. Define a class that inherits from `TestServer`.
3. Implement the `__init__` method and set up your custom hooks.

Here's an example of a custom test server that injects a context module:

```python
import types
from duck_test.test_server import TestServer

class ContextInjectorServer(TestServer):
    def __init__(self, processes, event_queue):
        super().__init__(processes, event_queue)
        self.setup_hooks()

    def setup_hooks(self):
        @self.hook_manager.register('after_import')
        def inject_context_module(context):
            # Create a new module to inject
            injected_module = types.ModuleType('duck_test_context')

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
            context['module'].__dict__['duck_test_context'] = injected_module

        @self.hook_manager.register('before_create_test')
        def setup_test_attributes(context):
            # Add attributes or methods to the test class
            context['test_class'].injected_attribute = "This is an injected attribute"
```

## Available Hooks

The TestServer class provides several hooks that you can use to customize the test execution process:

- `before_import`: Called before importing the test module
- `after_import`: Called after importing the test module
- `before_get_test_class`: Called before getting the test class from the module
- `after_get_test_class`: Called after getting the test class from the module
- `before_create_test`: Called before creating the test instance
- `after_create_test`: Called after creating the test instance
- `before_run_test`: Called before running the test
- `after_run_test`: Called after running the test

Each hook receives a `context` dictionary containing relevant information about the current test execution state.

## Using the Custom Test Server

To use your custom test server:

1. From the command line:

   ```
   duck-test -s ContextInjectorServer
   ```

2. Programmatically:

   ```python
   from duck_test import EventDrivenTestRunner
   from duck_test.test_servers.context_injector_server import ContextInjectorServer

   runner = EventDrivenTestRunner(processes=2, reporters=['DefaultReporter'], server=ContextInjectorServer)
   runner.discover_and_run('tests')
   ```

## Accessing Injected Context in Tests

Once you've set up your custom test server, you can access the injected context in your tests:

```python
from duck_test import EventDrivenTestCase

class TestWithInjectedContext(EventDrivenTestCase):
    def test_injected_context(self):
        # Access the injected module
        from duck_test_context import assert_eventually, config, event_publisher

        # Use the injected assert_eventually function
        def condition():
            return True  # Replace with actual condition

        assert_eventually(condition, timeout=2)

        # Access the injected configuration
        self.assertTrue(config.DEBUG)
        self.assertEqual(config.API_URL, "https://api.example.com")

        # Use the injected event publisher
        event_publisher.publish('custom_event', self.correlation_id, data="Custom event data")

        # Access the injected class attribute
        self.assertEqual(self.injected_attribute, "This is an injected attribute")
```

## Best Practices

1. Keep your custom test server focused on a specific purpose.
2. Use descriptive names for your test server and injected modules.
3. Document any injected functions, classes, or attributes for other developers.
4. Be cautious about modifying the test execution flow in hooks to maintain compatibility with the base TestServer.
5. Clean up any resources or side effects in the `after_run_test` hook if necessary.

By following these guidelines and using custom test servers, you can extend Duck Test to suit your specific testing needs while maintaining a clean and modular architecture.
