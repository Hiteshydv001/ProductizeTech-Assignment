import cv2
import numpy as np
import os
import re


def annotate_changes(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    """Return a copy of the after image with detected differences highlighted."""
    if before is None or after is None:
        raise ValueError("Input images must be valid numpy arrays.")

    if before.shape != after.shape:
        raise ValueError("Before and after images must share the same dimensions and channels.")

    # Convert to grayscale for difference computation
    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

    # Compute absolute difference
    diff = cv2.absdiff(before_gray, after_gray)

    # Threshold the difference
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    # Morphological dilation to merge close regions
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    # Find contours representing changes
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    annotated = after.copy()
    for cnt in contours:
        if cv2.contourArea(cnt) > 200:  # Ignore tiny noise
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 3)

    return annotated


def detect_changes(before_path, after_path, output_path):
    before = cv2.imread(before_path)
    after = cv2.imread(after_path)

    if before is None or after is None:
        raise ValueError(f"Unable to load images from {before_path} and/or {after_path}.")

    annotated = annotate_changes(before, after)

    cv2.imwrite(output_path, annotated)
    print(f"Processed -> {output_path}")

def main():
    input_folder = "input-images"
    output_folder = "task_2_output"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    files = os.listdir(input_folder)

    # Process only BEFORE images (X.jpg)
    for file in files:
        if re.match(r"^(.+)\.jpg$", file) and "~2" not in file:
            base_name = file.replace(".jpg", "")
            before_path = os.path.join(input_folder, file)
            after_file = f"{base_name}~2.jpg"
            after_path = os.path.join(input_folder, after_file)

            if os.path.exists(after_path):
                output_file = f"{base_name}~3.jpg"
                output_path = os.path.join(output_folder, output_file)
                detect_changes(before_path, after_path, output_path)
            else:
                print(f"[!] After image missing for: {file}")

if __name__ == "__main__":
    main()
