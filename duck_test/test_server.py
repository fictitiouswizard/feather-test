import multiprocessing
from multiprocessing import Pool
from duck_test.events import TestMessage, EventPublisher

class TestServer:
    def __init__(self, processes, event_queue):
        self.processes = processes
        self.event_queue = event_queue
        self.test_queue = multiprocessing.Manager().Queue()

    def start(self):
        with Pool(processes=self.processes) as pool:
            pool.map(self._run_test_process, range(self.processes))

    def add_test(self, test_message):
        self.test_queue.put(test_message.to_json())

    def _run_test_process(self, process_id):
        event_publisher = EventPublisher(self.event_queue)
        while not self.test_queue.empty():
            try:
                test_json = self.test_queue.get(block=False)
                test_message = TestMessage.from_json(test_json)
                self._run_single_test(test_message, event_publisher)
            except multiprocessing.queues.Empty:
                break

    def _run_single_test(self, test_message, event_publisher):
        # Import the test module
        module = __import__(test_message.module_name, fromlist=[test_message.class_name])
        test_class = getattr(module, test_message.class_name)
        
        # Create and run the test
        test = test_class(test_message.test_name)
        test.event_publisher = event_publisher
        test.run()
