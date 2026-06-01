import inspect
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(str(Path(__file__).parent))

# Import your app. Change 'app' if your variable name is different (e.g., 'api')
from app.main import app

print("--- SCANNING FASTAPI ROUTES AND DEPENDENCIES ---")
for route in app.routes:
    if hasattr(route, "endpoint"):
        # Check the main route function
        print(f"\nRoute: {route.methods} {route.path}")
        print(f"  Endpoint function: {route.endpoint.__name__}{inspect.signature(route.endpoint)}")
        
        # Check dependencies
        if hasattr(route, "dependant") and route.dependant.dependencies:
            for dep in route.dependant.dependencies:
                if hasattr(dep, "call") and dep.call:
                    try:
                        name = getattr(dep.call, "__name__", str(dep.call))
                        print(f"    -> Dependency: {name}{inspect.signature(dep.call)}")
                    except ValueError:
                        # Some built-in C functions don't support signature inspection
                        print(f"    -> Dependency: {dep.call} (Signature unreadable)")
