import torch

print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("CUDA version:", torch.version.cuda)
print("GPU count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("GPU name:", torch.cuda.get_device_name(0))
    print("GPU memory:", torch.cuda.get_device_properties(0).total_memory / 1024**3, "GB")

# Create a tensor on GPU
x = torch.randn(1000, 1000).cuda()
y = torch.randn(1000, 1000).cuda()

# Matrix multiplication on GPU
z = torch.matmul(x, y)

print("Computation successful on GPU!")
print("Result shape:", z.shape)
print("Device:", z.device)