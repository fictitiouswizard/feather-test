import multiprocessing
from multiprocessing import Pool
from functools import wraps
from feather_test.events import TestMessage, EventPublisher

class HookManager:
    def __init__(self):
        self.hooks = {
            'before_import': [],
            'after_import': [],
            'before_get_test_class': [],
            'after_get_test_class': [],
            'before_create_test': [],
            'after_create_test': [],
            'before_run_test': [],
            'after_run_test': [],
        }

    def register(self, hook_name):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            if hook_name not in self.hooks:
                raise ValueError(f"Unknown hook: {hook_name}")
            self.hooks[hook_name].append(wrapper)
            return wrapper
        return decorator

    def run_hooks(self, hook_name, context):
        if hook_name not in self.hooks:
            raise ValueError(f"Unknown hook: {hook_name}")
        for hook in self.hooks[hook_name]:
            try:
                hook(context)
            except Exception as e:
                print(f"Error in {hook_name} hook: {str(e)}")

class TestServer:
    def __init__(self, processes, event_queue):
        self.processes = processes
        self.event_queue = event_queue
        self.test_queue = multiprocessing.Manager().Queue()
        self.hook_manager = HookManager()

    def start(self):
        with Pool(processes=self.processes) as pool:
            pool.map(self._run_test_process, range(self.processes))

    def add_test(self, test_message):
        self.test_queue.put(test_message.to_json())

    def _run_test_process(self, process_id):
        event_publisher = EventPublisher(self.event_queue)
        while True:
            try:
                test_json = self.test_queue.get(block=False)
                test_message = TestMessage.from_json(test_json)
                self._run_single_test(test_message, event_publisher)
            except multiprocessing.queues.Empty:
                break

    def _run_single_test(self, test_message, event_publisher):
        context = {
            'test_message': test_message,
            'event_publisher': event_publisher,
            'module': None,
            'test_class': None,
            'test_instance': None
        }

        self.hook_manager.run_hooks('before_import', context)
        context['module'] = self._import_test_module(test_message)
        self.hook_manager.run_hooks('after_import', context)

        self.hook_manager.run_hooks('before_get_test_class', context)
        context['test_class'] = getattr(context['module'], test_message.class_name)
        self.hook_manager.run_hooks('after_get_test_class', context)

        self.hook_manager.run_hooks('before_create_test', context)
        context['test_instance'] = context['test_class'](test_message.test_name)
        context['test_instance'].set_event_publisher(event_publisher)  
        self.hook_manager.run_hooks('after_create_test', context)

        self.hook_manager.run_hooks('before_run_test', context)
        self._run_test(context['test_instance'])
        self.hook_manager.run_hooks('after_run_test', context)

    def _import_test_module(self, test_message):
        return __import__(test_message.module_name, fromlist=[test_message.class_name])

    def _run_test(self, test):
        if not hasattr(test, 'event_publisher') or test.event_publisher is None:
            raise ValueError("Test instance is missing event_publisher")
        test.run()
