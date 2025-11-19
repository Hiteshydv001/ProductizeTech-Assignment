import cv2
import numpy as np
import os

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FOLDER = "input-images"
CALIBRATION_FILE = "calibration_matrix.npy"

# Get the first pair of images to use for calibration
files = sorted([f for f in os.listdir(INPUT_FOLDER) if f.endswith("_Z.JPG")])
if not files:
    print("❌ No images found!")
    exit()

rgb_path = os.path.join(INPUT_FOLDER, files[0])
thermal_path = os.path.join(INPUT_FOLDER, files[0].replace("_Z.JPG", "_T.JPG"))

print(f"🔧 Calibrating using pair: {files[0]}")

# Load images
rgb_img = cv2.imread(rgb_path)
thermal_img = cv2.imread(thermal_path)

# Resize thermal to match RGB height (to make clicking easier/consistent)
h_rgb, w_rgb = rgb_img.shape[:2]
h_t, w_t = thermal_img.shape[:2]
scale_factor = h_rgb / h_t
new_w = int(w_t * scale_factor)
thermal_resized = cv2.resize(thermal_img, (new_w, h_rgb))

# Store points
rgb_points = []
thermal_points = []

def click_rgb(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        rgb_points.append((x, y))
        cv2.circle(rgb_img_display, (x, y), 10, (0, 255, 0), -1)
        cv2.putText(rgb_img_display, str(len(rgb_points)), (x+15, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("RGB Image (Click 4 points)", rgb_img_display)

def click_thermal(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        thermal_points.append((x, y))
        cv2.circle(thermal_img_display, (x, y), 10, (0, 0, 255), -1)
        cv2.putText(thermal_img_display, str(len(thermal_points)), (x+15, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Thermal Image (Click 4 points)", thermal_img_display)

# Prepare display images
rgb_img_display = rgb_img.copy()
thermal_img_display = thermal_resized.copy()

cv2.namedWindow("RGB Image (Click 4 points)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("RGB Image (Click 4 points)", 800, 600)
cv2.setMouseCallback("RGB Image (Click 4 points)", click_rgb)

cv2.namedWindow("Thermal Image (Click 4 points)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Thermal Image (Click 4 points)", 800, 600)
cv2.setMouseCallback("Thermal Image (Click 4 points)", click_thermal)

print("\n👉 INSTRUCTIONS:")
print("1. Click 4 distinct points on the RGB image (e.g., corners of objects).")
print("2. Click the SAME 4 points on the Thermal image in the SAME ORDER.")
print("3. Press any key when done.")

cv2.imshow("RGB Image (Click 4 points)", rgb_img_display)
cv2.imshow("Thermal Image (Click 4 points)", thermal_img_display)

cv2.waitKey(0)
cv2.destroyAllWindows()

# Check points
if len(rgb_points) < 4 or len(thermal_points) < 4:
    print("❌ Error: You must select at least 4 points on both images.")
    exit()

pts_rgb = np.float32(rgb_points[:4])
pts_thermal = np.float32(thermal_points[:4])

print("\nComputing alignment...")

# Calculate Affine Transform (Rotation, Scale, Translation)
# We use Affine instead of Homography to keep lines parallel (better for drones)
M = cv2.getAffineTransform(pts_thermal[:3], pts_rgb[:3])

# Save the matrix and the scale factor used
calibration_data = {
    "matrix": M,
    "scale_factor": scale_factor,
    "thermal_dims": (w_t, h_t),
    "rgb_dims": (w_rgb, h_rgb)
}

np.save(CALIBRATION_FILE, calibration_data)
print(f"✔ Calibration saved to {CALIBRATION_FILE}")
print("You can now run task_1_code.py")
