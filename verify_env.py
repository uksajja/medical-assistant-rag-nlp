import sys
import os
import chromadb
import numpy as np

print("=" * 60)
print("🚀 STARTING ENVIRONMENT HARDWARE ACCELERATION CHECK")
print("=" * 60)

# 1. Check Runtime Base
print(f"🔹 Python Version: {sys.version.split()[0]} (Expected: 3.12.x)")

# 2. Check System Env paths for your target versions
cuda_path = os.environ.get("CUDA_PATH", "NOT SET")
print(f"🔹 Target CUDA_PATH: {cuda_path}")

# 3. Test ChromaDB Engine Instantiation
try:
    client = chromadb.EphemeralClient()
    print("✅ ChromaDB: Initialized successfully (Using Ephemeral Client)")
except Exception as e:
    print(f"❌ ChromaDB: Failed to initialize. Error: {e}")

# 4. Test Local llama-cpp-python CUDA compilation bindings
try:
    from llama_cpp import Llama, llama_backend_init
    
    print("\n--- Testing llama-cpp-python Backend Bindings ---")
    # Query the compiled internal features of the llama-cpp library
    from llama_cpp import llama_supports_gpu_offload
    gpu_supported = llama_supports_gpu_offload()
    
    if gpu_supported:
        print("✅ llama-cpp-python: GPU compilation detected successfully!")
    else:
        print("⚠️  llama-cpp-python: Module loaded, but it appears compiled for CPU ONLY.")
        print("   -> Double-check your CMAKE_ARGS and environment paths during pip install.")
        
except ImportError:
    print("❌ llama-cpp-python: Module is not installed or cannot be imported.")
except Exception as e:
    print(f"❌ llama-cpp-python: Unexpected error during import testing: {e}")

print("=" * 60)
print("🏁 CHECK COMPLETE")
print("=" * 60)
