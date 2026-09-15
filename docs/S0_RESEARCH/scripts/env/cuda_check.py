import os, sys, traceback
import torch
print("torch", torch.__version__, "cuda build", torch.version.cuda, "cudnn", torch.backends.cudnn.version())
print("cuda.is_available", torch.cuda.is_available())
print("device", torch.cuda.get_device_name(0), "capability", torch.cuda.get_device_capability(0))
print("arch_list", torch.cuda.get_arch_list())
print("sm_75 in arch_list", "sm_75" in torch.cuda.get_arch_list())
print("CUBLAS_WORKSPACE_CONFIG =", os.environ.get("CUBLAS_WORKSPACE_CONFIG"))

def run(seed=0):
    torch.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    dev = "cuda"
    lstm = torch.nn.LSTM(input_size=6, hidden_size=32, num_layers=2, batch_first=True).to(dev)
    head = torch.nn.Linear(32, 1).to(dev)
    x = torch.randn(16, 50, 6, device=dev, requires_grad=True)
    y = torch.randn(16, 1, device=dev)
    out, _ = lstm(x)
    loss = torch.nn.functional.mse_loss(head(out[:, -1]), y)
    loss.backward()
    g = sum(p.grad.double().abs().sum().item() for p in lstm.parameters())
    return loss.item(), g, x.grad.double().abs().sum().item()

try:
    r1 = run(); r2 = run()
    print("LSTM fwd+bwd OK", r1)
    print("bitwise identical across two runs:", r1 == r2)
except Exception as e:
    print("LSTM FAILED:", type(e).__name__, str(e).splitlines()[0:6])
