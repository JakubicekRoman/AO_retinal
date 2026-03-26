"""Compare PNG files in images and masks folders.

Exit codes:
  0 - masks match images (skip segmentation)
  1 - masks do NOT match images (run segmentation)
"""

import sys
import os
import argparse


def compare_folders(images_dir: str, masks_dir: str) -> bool:
    """Return True if masks folder contains the same PNG filenames as images folder."""
    if not os.path.isdir(masks_dir):
        print(f"Masks folder does not exist: {masks_dir}")
        return False

    image_pngs = {f for f in os.listdir(images_dir) if f.lower().endswith(".png")}
    mask_pngs = {f for f in os.listdir(masks_dir) if f.lower().endswith(".png")}

    if not image_pngs:
        print("No PNG files found in images folder.")
        return False

    if image_pngs == mask_pngs:
        print(f"Masks match: {len(image_pngs)} PNG files are identical in both folders.")
        return True

    missing = image_pngs - mask_pngs
    extra = mask_pngs - image_pngs
    if missing:
        print(f"Missing in masks ({len(missing)}): {', '.join(sorted(missing)[:5])}{'...' if len(missing) > 5 else ''}")
    if extra:
        print(f"Extra in masks ({len(extra)}): {', '.join(sorted(extra)[:5])}{'...' if len(extra) > 5 else ''}")
    print(f"Images: {len(image_pngs)}, Masks: {len(mask_pngs)} -> mismatch.")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare PNG files in images vs masks folders.")
    parser.add_argument("-i", "--images", required=True, help="Path to images folder")
    parser.add_argument("-m", "--masks", required=True, help="Path to masks folder")
    args = parser.parse_args()

    match = compare_folders(args.images, args.masks)
    sys.exit(0 if match else 1)
