import os
import cv2
import shutil
import numpy as np

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
INPUT_FOLDER = "input-images"
OUTPUT_FOLDER = "task_1_output"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------------------------------------------
# HELPER: Manual Point Selection
# ---------------------------------------------------
def get_manual_alignment(rgb_img, thermal_img, filename):
    """
    Opens a GUI for the user to click 3 corresponding points on RGB and Thermal images.
    Returns the aligned thermal image (640x512).
    """
    # TARGET DIMENSIONS
    TARGET_W, TARGET_H = 640, 512

    # Resize RGB to target dimensions (distorted to fit 640x512)
    rgb_resized = cv2.resize(rgb_img, (TARGET_W, TARGET_H))
    
    # Thermal is already 640x512 (or should be)
    # If not, we resize it or keep it? 
    # Assuming thermal input is 640x512. If not, we use it as is for source points.
    h_t, w_t = thermal_img.shape[:2]
    
    # State for mouse callbacks
    rgb_points = []
    thermal_points = []
    
    # Display copies
    rgb_display = rgb_resized.copy()
    thermal_display = thermal_img.copy()

    def click_rgb(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(rgb_points) < 3:
                rgb_points.append((x, y))
                cv2.circle(rgb_display, (x, y), 5, (0, 255, 0), -1)
                cv2.putText(rgb_display, str(len(rgb_points)), (x+10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.imshow(f"RGB (Target): {filename}", rgb_display)

    def click_thermal(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(thermal_points) < 3:
                thermal_points.append((x, y))
                cv2.circle(thermal_display, (x, y), 5, (0, 0, 255), -1)
                cv2.putText(thermal_display, str(len(thermal_points)), (x+10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                cv2.imshow(f"Thermal (Source): {filename}", thermal_display)

    # Setup Windows
    cv2.namedWindow(f"RGB (Target): {filename}", cv2.WINDOW_NORMAL)
    cv2.resizeWindow(f"RGB (Target): {filename}", 800, 600)
    cv2.setMouseCallback(f"RGB (Target): {filename}", click_rgb)

    cv2.namedWindow(f"Thermal (Source): {filename}", cv2.WINDOW_NORMAL)
    cv2.resizeWindow(f"Thermal (Source): {filename}", 800, 600)
    cv2.setMouseCallback(f"Thermal (Source): {filename}", click_thermal)

    # Initial Show
    cv2.imshow(f"RGB (Target): {filename}", rgb_display)
    cv2.imshow(f"Thermal (Source): {filename}", thermal_display)

    print(f"\n--- Aligning {filename} ---")
    print("👉 Click 3 matching points on RGB (Left/Target), then 3 on Thermal (Right/Source).")
    print("   (Press 'r' to reset points, 'q' to skip/abort this image)")

    while True:
        key = cv2.waitKey(100) & 0xFF
        
        # Check if done
        if len(rgb_points) == 3 and len(thermal_points) == 3:
            print("✔ Points captured. Computing transform...")
            break
        
        if key == ord('r'):
            rgb_points = []
            thermal_points = []
            rgb_display = rgb_resized.copy()
            thermal_display = thermal_img.copy()
            cv2.imshow(f"RGB (Target): {filename}", rgb_display)
            cv2.imshow(f"Thermal (Source): {filename}", thermal_display)
            print("🔄 Reset points.")

        if key == ord('q'):
            print("⚠ Skipped.")
            cv2.destroyAllWindows()
            return None

    cv2.destroyAllWindows()

    # Compute Affine Transform
    pts_rgb = np.float32(rgb_points)
    pts_thermal = np.float32(thermal_points)
    
    # We want to map Thermal (Source) -> RGB (Target)
    M = cv2.getAffineTransform(pts_thermal, pts_rgb)
    
    # Apply transform
    # Output size is TARGET_W, TARGET_H (640, 512)
    aligned = cv2.warpAffine(thermal_img, M, (TARGET_W, TARGET_H), 
                             flags=cv2.INTER_LINEAR, 
                             borderMode=cv2.BORDER_CONSTANT, 
                             borderValue=(0, 0, 0))
    return aligned


# ---------------------------------------------------
# MAIN: process all pairs
# ---------------------------------------------------
def process_all():
    files = sorted([f for f in os.listdir(INPUT_FOLDER) if f.endswith("_Z.JPG")])
    if not files:
        print(f"❌ No RGB images with suffix '_Z.JPG' found in {INPUT_FOLDER}")
        return

    print(f"🚀 Found {len(files)} RGB images.")
    print("Starting manual alignment process...")

    for rgb_file in files:
        base_id = rgb_file.replace("_Z.JPG", "")
        rgb_path = os.path.join(INPUT_FOLDER, rgb_file)
        thermal_name = base_id + "_T.JPG"
        thermal_path = os.path.join(INPUT_FOLDER, thermal_name)

        # 1. Always copy RGB to output (Requirement)
        out_rgb = os.path.join(OUTPUT_FOLDER, rgb_file)
        shutil.copy2(rgb_path, out_rgb)

        # 2. Check for Thermal
        if not os.path.exists(thermal_path):
            print(f"[INFO] No thermal image for {base_id} (RGB copied).")
            continue

        # 3. Process Pair
        rgb_img = cv2.imread(rgb_path)
        thermal_img = cv2.imread(thermal_path)

        if rgb_img is None or thermal_img is None:
            print(f"[ERROR] Could not read images for {base_id}")
            continue

        # Perform Manual Alignment
        aligned_img = get_manual_alignment(rgb_img, thermal_img, base_id)

        if aligned_img is not None:
            out_thermal = os.path.join(OUTPUT_FOLDER, base_id + "_AT.JPG")
            cv2.imwrite(out_thermal, aligned_img)
            print(f"✔ Saved aligned thermal: {out_thermal}")
        else:
            print(f"❌ Failed to align {base_id}")

    print("\n🎯 All done! Check task_1_output/")

if __name__ == "__main__":
    process_all()
