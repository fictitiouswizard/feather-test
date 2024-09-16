import sys
import os
import argparse
from feather_test import EventDrivenTestRunner
from feather_test.utils import to_snake_case

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
    parser.add_argument('-r', '--reporter', default='ConsoleReporter',
                        help='Reporter to use (default: ConsoleReporter)')
    parser.add_argument('-s', '--server', default='TestServer',
                        help='Test server to use (default: TestServer)')
    
    # Parse known args first
    args, unknown = parser.parse_known_args()

    # Process unknown args for reporter-specific options
    reporter_args = {}
    i = 0
    while i < len(unknown):
        """
        This while loop processes unknown arguments to handle reporter-specific options.
        
        It iterates through the unknown arguments, looking for options that match the
        pattern '--<reporter_name>-<option_name>'. When found, it adds these options
        to the reporter_args dictionary.

        The loop works as follows:
        1. Check if the current argument starts with '--'.
        2. If it does, split the argument into parts using '-' as a separator.
        3. If there are at least two parts and the first part (lowercase) matches
           the specified reporter name (lowercase), process it as a reporter option.
        4. If the next argument exists, use it as the option value; otherwise, set it to True.
        5. Add the option to the reporter_args dictionary.
        6. Increment the loop counter accordingly (by 2 if a value was found, by 1 otherwise).

        This allows users to specify reporter-specific options in the CLI, which will
        be passed to the chosen reporter during initialization.
        """
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
    
    # Apply reporter-specific arguments
    if reporter_args:
        reporter_class = getattr(runner, f"_{to_snake_case(args.reporter)}")
        for key, value in reporter_args.items():
            setattr(reporter_class, key, value)

    # Discover and run tests
    runner.discover_and_run(start_dir=args.directory, pattern=args.pattern)

if __name__ == '__main__':
    main()
