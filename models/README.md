# Detection model

This project uses the classic MobileNet-SSD Caffe model (trained on Pascal
VOC's 20 classes + background), run via OpenCV's DNN module. It needs two
files placed in this directory (both gitignored — see `.gitignore` — the
`.caffemodel` weights are a ~23MB binary that shouldn't go in git):

- `MobileNetSSD_deploy.prototxt` — the network architecture (small text file).
- `MobileNetSSD_deploy.caffemodel` — the trained weights.

These are widely mirrored (e.g. the `chuanqi305/MobileNet-SSD` GitHub repo,
which is the original training repo, or any of the many OpenCV
person-detection tutorials that redistribute the same two files). Clone or
download from a source you trust, verify the prototxt's class list matches
`PERSON_CLASS_ID = 15` in `src/mimamori/detector.py` (index 15 should be
"person" in a 21-class VOC list), and place both files here.

If you'd rather use a different/newer model (e.g. a COCO-trained one), keep
the two-file (prototxt + weights) shape and update `config/config.yaml`
(`detection.model_prototxt` / `model_weights`) plus `PERSON_CLASS_ID` in
`detector.py` to match its label order.

## Calibrating regions and door state

Both `config/regions.yaml` (region polygons) and `config/config.yaml`
(`door.closed_edge_density` / `open_edge_density`) currently hold placeholder
values and must be calibrated on-device:

1. Save a snapshot at the camera's configured resolution (see
   `camera.size` in `config.yaml`), e.g.:
   ```
   rpicam-still -o snapshot.jpg --width 1296 --height 972
   ```
2. Open it in any image viewer that shows pixel coordinates (e.g. GIMP) and
   read off the corner points of the door, bed, sofa, and table areas.
   Enter them into `config/regions.yaml` as `[x, y]` polygon points.
3. For the door, take one snapshot with it closed and one with it open,
   crop to the door's region, and compute the Canny edge density for each
   (this is exactly what `mimamori.door.edge_density` does — a short REPL
   snippet using that function on each cropped ROI is the quickest way).
   Put the closed frame's value in `door.closed_edge_density` and the open
   frame's in `door.open_edge_density`.
