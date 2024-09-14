import sys
import os
import argparse
from duck_test import EventDrivenTestRunner
from duck_test.event_driven_unittest import to_snake_case

def main():
    parser = argparse.ArgumentParser(description='Run tests using the Duck Test framework.')
    parser.add_argument('start_dir', nargs='?', default='.',
                        help='Directory to start discovery (default: current directory)')
    parser.add_argument('-p', '--pattern', default='test*.py',
                        help='Pattern to match test files (default: test*.py)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('-f', '--failfast', action='store_true',
                        help='Stop on first fail or error')
    parser.add_argument('-c', '--catch', action='store_true',
                        help='Catch control-C and display results')
    parser.add_argument('-b', '--buffer', action='store_true',
                        help='Buffer stdout and stderr during tests')
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
                if i + 1 < len(unknown) and not unknown[i+1].startswith('--'):
                    reporter_args[parts[1]] = unknown[i+1]
                    i += 1
                else:
                    reporter_args[parts[1]] = True
        i += 1

    # Ensure the start directory is in the Python path
    start_dir = os.path.abspath(args.start_dir)
    if start_dir not in sys.path:
        sys.path.insert(0, start_dir)

    # Create and configure the test runner
    runner = EventDrivenTestRunner(
        processes=args.processes,
        verbosity=2 if args.verbose else 1,
        reporters=[(args.reporter, reporter_args)],
        failfast=args.failfast,
        buffer=args.buffer,
        catch_interrupt=args.catch
    )

    # Discover and run tests
    suite = runner.discover_and_run(
        start_dir=start_dir,
        pattern=args.pattern
    )

if __name__ == '__main__':
    main()
