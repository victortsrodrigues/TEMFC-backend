import argparse


def run_api_mode(host: str = '0.0.0.0', port: int = 5000, debug: bool = False) -> None:
    # Import here to avoid circular imports
    from controllers.controller import run_api
    run_api(host, port, debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the professional data processor')
    parser.add_argument('--api', action='store_true', help='Run as API server')
    parser.add_argument('--host', default='0.0.0.0', help='API server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='API server port (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Run API server in debug mode')
    
    args = parser.parse_args()
    
    args.api = True
    
    if args.api:
        run_api_mode(args.host, args.port, args.debug)