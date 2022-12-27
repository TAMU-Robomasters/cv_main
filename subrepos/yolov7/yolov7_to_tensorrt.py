import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, help="path to .pt model file")
    parser.add_argument("--conf", type=float, default=0.25, help="confidence threshold for NMS")
    parser.add_argument("--img-size", type=int, default=416, help="image size")

    args = parser.parse_args()
    model_path = args.model_path
    conf = args.conf
    img_size = args.img_size

    # split extension from model path
    model_path, ext = os.path.splitext(model_path)
    # get file name from model path
    model_name = os.path.basename(model_path)
    
    # try:
    #     print(f"Converting model {model_path}{ext} to ONNX...")
    #     os.system(f"python3 export.py --weights ./{model_path}{ext} --grid --end2end --simplify --topk-all 100 --iou-thres 0.65 --conf-thres {conf} --img-size {img_size} {img_size} --device 0")
    # except Exception as e:
    #     raise e

    # try:
    #     print("Cloning TensorRT repo...")
    #     os.system("rm -rf TensorRT-For-YOLO-Series")
    #     os.system("git clone https://github.com/bid-p/TensorRT-For-YOLO-Series.git")
    # except Exception as e:
    #     raise e
    
    try:
        print("Converting ONNX to TensorRT...")
        os.system(f"python3 ./TensorRT-For-YOLO-Series/export.py -o {model_path}.onnx -e {model_path}.trt -p fp16 --verbose")
    except Exception as e:
        raise e