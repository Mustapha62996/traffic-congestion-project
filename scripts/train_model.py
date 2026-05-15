from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_service.training import train_and_save_model


if __name__ == "__main__":
    result = train_and_save_model()
    print(json.dumps(result.__dict__, indent=2))
