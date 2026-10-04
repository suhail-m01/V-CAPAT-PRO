# Optional beacon-specific ONNX weights

`yolov8n_beacon.onnx` is intentionally **not** fabricated or included: there is no
beacon-trained model in this repository. To enable the optional ONNX detector,
export a legitimately trained beacon detector to this filename. The OpenCV-DNN
adapter in `vcapat/detection/yolo_onnx.py` expects N×5 rows of bounding box
coordinates and confidence in model-input pixels; adapt its output decoding for
your model's actual schema. The default four CV methods need no weights.
