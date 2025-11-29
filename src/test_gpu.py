import torch
from langchain_community.embeddings import HuggingFaceEmbeddings

MODEL_NAME = "dunzhang/stella_en_1.5B_v5"
device = "cuda"

print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"Device Name: {torch.cuda.get_device_name(0)}")

try:
    print("Loading model with HuggingFaceEmbeddings (trust_remote_code=True)...")
    embeddings = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={"device": device, "trust_remote_code": True},
        encode_kwargs={"normalize_embeddings": True}
    )
    
    print("Generating embedding...")
    text = "This is a test sentence to verify GPU acceleration."
    vector = embeddings.embed_query(text)
    print(f"Success! Vector length: {len(vector)}")
except Exception as e:
    print(f"FAILED: {e}")
