import argparse
import logging
from multiprocessing import freeze_support
import os
import sys
from feather_test import EventDrivenTestRunner
from feather_test.utils.reporter_loader import load_reporter
from feather_test.utils.string_utils import to_snake_case

default_log_level = os.environ.get('FEATHER_LOG_LEVEL', 'WARNING')

logging.basicConfig(
    level=getattr(logging, default_log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("feather_test")

def parse_reporter_args(unknown_args, reporters):
    """
    Parse unknown arguments to handle reporter-specific options.

    Args:
        unknown_args (list): List of unknown command-line arguments.
        reporters (list): List of reporter names.

    Returns:
        dict: A dictionary of reporter-specific arguments.
    """
    reporter_args = {reporter: {} for reporter in reporters}
    i = 0
    while i < len(unknown_args):
        arg = unknown_args[i]
        if arg.startswith('--'):
            parts = arg[2:].split('-', 1)
            if len(parts) == 2:
                reporter_name = parts[0].lower()
                for full_reporter_name in reporters:
                    if full_reporter_name.lower().startswith(reporter_name):
                        key = to_snake_case(parts[1])
                        if i + 1 < len(unknown_args) and not unknown_args[i+1].startswith('--'):
                            reporter_args[full_reporter_name][key] = unknown_args[i+1]
                            i += 1
                        else:
                            reporter_args[full_reporter_name][key] = True
                        break
        i += 1
    return reporter_args

def main():
    """
    The main entry point for the Feather Test CLI.

    This function parses command-line arguments, configures the test runner,
    and initiates the test discovery and execution process.
    """
    parser = argparse.ArgumentParser(description='Run tests using the Feather Test framework.')
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
    parser.add_argument('-r', '--reporters', nargs='+', default=['ConsoleReporter'],
                        help='Reporter to use (default: ConsoleReporter)')
    parser.add_argument('-s', '--server', default='TestServer',
                        help='Test server to use (default: TestServer)')
    
    # Parse known args first
    args, unknown = parser.parse_known_args()

    # Process unknown args for reporter-specific options
    reporter_args = parse_reporter_args(unknown, args.reporters)

    reporter_args = {
        reporter_name: {k.replace('-', '_'): v for k, v in args.items()}
        for reporter_name, args in reporter_args.items()
    }

    # Initialize reporters
    reporters = []
    if isinstance(args.reporters, str):
        args.reporters = [args.reporters]
    for reporter_name in args.reporters:
        reporter = load_reporter(reporter_name, **reporter_args[reporter_name])
        reporters.append(reporter)

    # Create and run the test runner
    runner = EventDrivenTestRunner(reporters=reporters)
    runner.discover_and_run(start_dir=args.directory, pattern=args.pattern)

if __name__ == "__main__":
    freeze_support()
    main()
