"""Make the sdsb modules importable from tests/ without packaging.

pytest loads this conftest (it is an ancestor of tests/) before collecting,
so the insert below guarantees `import sources`, `import shopify_catalog`,
etc. resolve to the modules in this directory regardless of the CWD.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
