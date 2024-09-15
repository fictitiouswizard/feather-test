import sys
import os
import argparse
from duck_test import EventDrivenTestRunner
from duck_test.event_driven_unittest import to_snake_case

def main():
    parser = argparse.ArgumentParser(description='Run tests using the Duck Test framework.')
    parser.add_argument('-d', '--directory', default='.',
                        help='Directory to start discovery (default: current directory)')
    parser.add_argument('-p', '--pattern', default='test*.py',
                        help='Pattern to match test files (default: test*.py)')
    parser.add_argument('-f', '--failfast', action='store_true',
                        help='Stop on first fail or error')
    parser.add_argument('-c', '--catch', action='store_true',
                        help='Catch control-C and display results')
    parser.add_argument('-k', '--processes', type=int, default=1,
                        help='Number of processes to use')
    parser.add_argument('-r', '--reporter', default='DefaultReporter',
                        help='Reporter to use (default: DefaultReporter)')
    
    # Parse known args first
    args, unknown = parser.parse_known_args()

    # Process unknown args for reporter-specific options
    reporter_args = {}
    i = 0
    while i < len(unknown):
        arg = unknown[i]
        if arg.startswith('--'):
            parts = arg[2:].split('-', 1)
            if len(parts) == 2 and parts[0].lower() == args.reporter.lower():
                key = parts[1]
                if i + 1 < len(unknown):
                    reporter_args[key] = unknown[i+1]
                    i += 1
                else:
                    reporter_args[key] = True
        i += 1

    # Ensure the start directory is in the Python path
    start_dir = os.path.abspath(args.directory)
    if start_dir not in sys.path:
        sys.path.insert(0, start_dir)

    # Create and configure the test runner
    runner = EventDrivenTestRunner(processes=args.processes, reporters=[args.reporter])
    runner.discover_and_run(start_dir=args.directory, pattern=args.pattern)

if __name__ == '__main__':
    main()
