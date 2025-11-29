import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Prefix: {sys.prefix}")
print(f"Base Prefix: {sys.base_prefix}")
print(f"Is Isolated Venv: {sys.prefix != sys.base_prefix}")

try:
    import torch
    print(f"Torch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
except ImportError as e:
    print(f"Torch Import Failed: {e}")

try:
    import transformers
    print(f"Transformers Version: {transformers.__version__}")
except ImportError as e:
    print(f"Transformers Import Failed: {e}")

try:
    import chromadb
    print(f"ChromaDB Version: {chromadb.__version__}")
except ImportError as e:
    print(f"ChromaDB Import Failed: {e}")
