import torch

if __name__ == "__main__":
    model = torch.hub.load(repo_or_dir='bidp/yolov7', model='custom', trust_repo=True, pretrained=True).eval()
    traced_graph = torch.jit.trace(model, torch.randn(1, 3, 416, 416))
    traced_graph.save("yolov7_deeplab.pth")