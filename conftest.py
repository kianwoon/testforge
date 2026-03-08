import sys
from pathlib import Path

# Add module directories to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "agent"))
sys.path.insert(0, str(project_root / "bot"))
