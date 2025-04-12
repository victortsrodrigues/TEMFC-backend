import argparse
import os

def run_development_server(host='0.0.0.0', port=5000, debug=False):
    """
    Run Flask development server.
    
    Args:
        host: Host address to bind the server.
        port: Port number to run the server.
        debug: Whether to run the server in debug mode.
    """
    from app import create_app
    app = create_app()
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the professional data processor')
    parser.add_argument('--host', default='0.0.0.0', help='Server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 5000)), 
                        help='Server port (default: 5000 or PORT env variable)')
    parser.add_argument('--debug', action='store_true', help='Run server in debug mode')
    
    args = parser.parse_args()
    
    run_development_server(args.host, args.port, args.debug)