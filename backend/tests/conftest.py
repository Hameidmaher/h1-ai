import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture(scope="session", autouse=True)
def init_knowledge():
    from knowledge.engine import advisory_engine
    advisory_engine.initialize()
    yield
