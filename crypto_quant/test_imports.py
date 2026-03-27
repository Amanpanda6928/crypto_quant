#!/usr/bin/env python3

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    import backend.api.routes.signals
    print('✓ signals OK')
except Exception as e:
    print(f'✗ signals failed: {e}')

try:
    import backend.api.routes.market
    print('✓ market OK')
except Exception as e:
    print(f'✗ market failed: {e}')

try:
    import backend.api.routes.performance
    print('✓ performance OK')
except Exception as e:
    print(f'✗ performance failed: {e}')

try:
    import backend.api.websocket.manager
    print('✓ websocket OK')
except Exception as e:
    print(f'✗ websocket failed: {e}')

try:
    import backend.api.websocket.stream
    print('✓ stream OK')
except Exception as e:
    print(f'✗ stream failed: {e}')

try:
    import backend.api.schemas.signal
    print('✓ schemas OK')
except Exception as e:
    print(f'✗ schemas failed: {e}')

try:
    import backend.core.performance_tracker
    print('✓ tracker OK')
except Exception as e:
    print(f'✗ tracker failed: {e}')

try:
    import backend.core.state_manager
    print('✓ state OK')
except Exception as e:
    print(f'✗ state failed: {e}')

try:
    import backend.data.binance_fetcher
    print('✓ fetcher OK')
except Exception as e:
    print(f'✗ fetcher failed: {e}')

print('All imports completed!')