import os
import cv2
import shutil
import numpy as np

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
INPUT_FOLDER = "input-images"
OUTPUT_FOLDER = "task_1_output"
CALIBRATION_FILE = "calibration_matrix.npy"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------------------------------------------
# MAIN: process all pairs
# ---------------------------------------------------
def process_all():
    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith("_Z.JPG")]
    if not files:
        print(f"❌ No RGB images with suffix '_Z.JPG' found in {INPUT_FOLDER}")
        return

    # Load calibration if available
    calibration = None
    if os.path.exists(CALIBRATION_FILE):
        print(f"✔ Found calibration file: {CALIBRATION_FILE}")
        calibration = np.load(CALIBRATION_FILE, allow_pickle=True).item()
    else:
        print("⚠ No calibration file found! Please run calibrate_manual.py first.")
        print("  (Falling back to simple center-crop, which is likely wrong)")

    print(f"🚀 Processing {len(files)} pairs...")

    for rgb_file in sorted(files):
        base_id = rgb_file.replace("_Z.JPG", "")
        rgb_path = os.path.join(INPUT_FOLDER, rgb_file)
        thermal_name = base_id + "_T.JPG"
        thermal_path = os.path.join(INPUT_FOLDER, thermal_name)

        if not os.path.exists(thermal_path):
            print(f"[WARN] Thermal image missing for {rgb_file} – skipping.")
            # Still copy RGB into output
            shutil.copy2(rgb_path, os.path.join(OUTPUT_FOLDER, rgb_file))
            continue

        # Load images
        rgb_img = cv2.imread(rgb_path)
        thermal_img = cv2.imread(thermal_path)

        if rgb_img is None or thermal_img is None:
            print(f"[ERROR] Failed to read pair: {rgb_file}")
            continue

        h_rgb, w_rgb = rgb_img.shape[:2]
        h_t, w_t = thermal_img.shape[:2]

        aligned = None

        if calibration:
            # 1. Resize thermal using the SAME scale factor as calibration
            scale_factor = calibration["scale_factor"]
            new_w = int(w_t * scale_factor)
            thermal_resized = cv2.resize(thermal_img, (new_w, h_rgb))

            # 2. Apply the Affine Transform
            M = calibration["matrix"]
            aligned = cv2.warpAffine(thermal_resized, M, (w_rgb, h_rgb), 
                                     flags=cv2.INTER_LINEAR, 
                                     borderMode=cv2.BORDER_CONSTANT, 
                                     borderValue=(0, 0, 0))
        else:
            # Fallback: Center + Scale (Simple)
            scale = min(w_rgb / w_t, h_rgb / h_t)
            new_w, new_h = int(w_t * scale), int(h_t * scale)
            resized = cv2.resize(thermal_img, (new_w, new_h))
            
            canvas = np.zeros((h_rgb, w_rgb, 3), dtype=np.uint8)
            x_off = (w_rgb - new_w) // 2
            y_off = (h_rgb - new_h) // 2
            canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
            aligned = canvas

        # Save outputs
        out_thermal = os.path.join(OUTPUT_FOLDER, base_id + "_AT.JPG")
        cv2.imwrite(out_thermal, aligned)

        # Copy RGB
        out_rgb = os.path.join(OUTPUT_FOLDER, rgb_file)
        if not os.path.exists(out_rgb):
            shutil.copy2(rgb_path, out_rgb)
            
        print(f"Processed: {base_id}")

    print("\n🎯 Done. Check outputs in:", OUTPUT_FOLDER)


if __name__ == "__main__":
    process_all()
