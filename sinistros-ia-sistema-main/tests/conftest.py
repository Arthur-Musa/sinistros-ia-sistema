import sys
import types

# Stub 'swarm' if missing
if 'swarm' not in sys.modules:
    swarm_stub = types.ModuleType('swarm')
    class DummyAgent:
        def __init__(self, name=None, model=None, instructions=None, tools=None, functions=None):
            self.name = name
    class DummySwarm:
        def __init__(self, *args, **kwargs):
            pass
        def run(self, agent=None, messages=None):
            return types.SimpleNamespace(
                messages=[{"content": "Stub response"}],
                agent=types.SimpleNamespace(name=getattr(agent, 'name', 'stub'))
            )
    swarm_stub.Agent = DummyAgent
    def Swarm(*args, **kwargs):
        return DummySwarm()
    swarm_stub.Swarm = Swarm
    sys.modules['swarm'] = swarm_stub

# Stub 'fastapi' and key submodules if missing
if 'fastapi' not in sys.modules:
    fastapi_stub = types.ModuleType('fastapi')
    class FastAPI:
        def __init__(self, *args, **kwargs):
            self.routes = []
        def add_api_route(self, path, endpoint, methods=None, **kwargs):
            self.routes.append((path, methods))
        # decorators
        def get(self, path, **kwargs):
            def decorator(func):
                self.add_api_route(path, func, methods=["GET"])
                return func
            return decorator
        def post(self, path, **kwargs):
            def decorator(func):
                self.add_api_route(path, func, methods=["POST"])
                return func
            return decorator
        def add_middleware(self, middleware_class, **kwargs):
            pass
    class HTTPException(Exception):
        pass
    class BackgroundTasks:
        pass
    def Depends(x=None):
        pass
    fastapi_stub.FastAPI = FastAPI
    fastapi_stub.HTTPException = HTTPException
    fastapi_stub.BackgroundTasks = BackgroundTasks
    fastapi_stub.Depends = Depends
    # Prepare submodules
    responses = types.ModuleType('fastapi.responses')
    responses.JSONResponse = lambda *a, **k: None
    middleware = types.ModuleType('fastapi.middleware')
    cors = types.ModuleType('fastapi.middleware.cors')
    cors.CORSMiddleware = lambda *a, **k: None
    middleware.cors = cors
    fastapi_stub.responses = responses
    fastapi_stub.middleware = middleware
    sys.modules['fastapi'] = fastapi_stub
    sys.modules['fastapi.responses'] = responses
    sys.modules['fastapi.middleware'] = middleware
    sys.modules['fastapi.middleware.cors'] = cors
