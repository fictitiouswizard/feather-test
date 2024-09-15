import unittest
import subprocess
import sys
import os
import json

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.cli_path = os.path.join(os.path.dirname(__file__), '..', 'duck_test', 'cli.py')
        self.sample_tests_dir = os.path.join(os.path.dirname(__file__), 'sample_tests')
        self.output_dir = 'e2e_test_output'
        os.makedirs(self.output_dir, exist_ok=True)

    def run_cli(self, args):
        command = [sys.executable, self.cli_path] + args
        result = subprocess.run(command, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

    def test_end_to_end(self):
        returncode, stdout, stderr = self.run_cli([
            '-r', 'JsonReporter',
            f'--jsonreporter-output-dir={self.output_dir}',
            '--jsonreporter-filename=e2e_test_run.json',
            self.sample_tests_dir
        ])
        print(stderr)
        self.assertEqual(returncode, 0)
        self.assertIn('Test run completed', stdout)

        # Check if JSON file was created and contains expected data
        json_file = os.path.join(self.output_dir, 'e2e_test_run.json')
        self.assertTrue(os.path.exists(json_file))

        with open(json_file, 'r') as f:
            data = json.load(f)

        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['event_type'], 'test_run_start')
        self.assertEqual(data[-1]['event_type'], 'test_run_end')

    def tearDown(self):
        # Clean up the output directory
        for file in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, file))
        os.rmdir(self.output_dir)

if __name__ == '__main__':
    unittest.main()