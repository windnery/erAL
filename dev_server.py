from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

from api import Api
from game_engine.logging_config import configure_logging


FRONTEND_DIR = Path(__file__).parent / 'frontend'


def create_app(api: Api | None = None) -> Flask:
    """Create and configure the Flask development server app."""
    app = Flask(
        __name__,
        static_folder=str(FRONTEND_DIR),
        static_url_path='',
    )
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    if api is None:
        api = Api()
    game_api = api

    @app.after_request
    def add_no_cache_headers(response):
        """Prevent browser caching during development."""
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        return response

    @app.route('/')
    def index():
        """Serve the main frontend entrypoint."""
        return send_from_directory(FRONTEND_DIR, 'index.html')

    @app.route('/api/call', methods=['POST'])
    def api_call():
        """Dispatch frontend API requests through the unified Api manager."""
        payload = request.get_json(force=True, silent=True) or {}
        manager_name = payload.get('manager')
        func_name = payload.get('func')
        args = payload.get('args', [])
        kwargs = payload.get('kwargs', {})

        if not manager_name or not func_name:
            return jsonify({
                'success': False,
                'error': "Both 'manager' and 'func' are required",
            }), 400

        try:
            result = game_api.call(manager_name, func_name, *args, **kwargs)
            return jsonify({
                'success': True,
                'result': result,
            })
        except Exception as error:
            return jsonify({
                'success': False,
                'error': str(error),
            }), 500

    @app.route('/api/report_error', methods=['POST'])
    def report_error():
        """Receive and forward frontend error reports to game engine logging."""
        payload = request.get_json(force=True, silent=True) or {}
        game_api.report_frontend_error(
            message=payload.get('message', 'Unknown frontend error'),
            source=payload.get('source', ''),
            line=payload.get('line'),
            column=payload.get('column'),
            stack=payload.get('stack', ''),
        )
        return jsonify({'success': True})

    return app


def main():
    configure_logging()
    app = create_app()
    port = 5000
    print(f'Starting erAL Flask Dev Server on http://127.0.0.1:{port} ...')
    print('Open your browser and navigate to the above URL for development.')
    app.run(host='127.0.0.1', port=port, debug=True)


if __name__ == '__main__':
    main()
