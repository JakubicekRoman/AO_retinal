#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vessel wall analysis module for retinal AO images.
Ports MATLAB functions to Python with NumPy/SciPy optimization.
"""

import numpy as np
from scipy import ndimage
from scipy.signal.windows import gaussian
from scipy.ndimage import distance_transform_edt, label, find_objects
from skimage import morphology, measure, restoration
from skimage.measure import regionprops
import imageio.v3 as iio
from pathlib import Path
import pandas as pd
from PIL import Image, ImageDraw
from skimage.morphology import medial_axis, skeletonize


def load_images(path_data, path_masks):
    """
    Load image and mask pairs from directories.
    
    Args:
        path_data: Directory with original images
        path_masks: Directory with segmentation masks
        
    Yields:
        Tuples of (image_array, mask_array, filename)
    """
    data_path = Path(path_data)
    mask_path = Path(path_masks)
    
    for img_file in sorted(data_path.glob('*.png')):
        # Find corresponding mask (replace _0000 if present)
        mask_name = img_file.name.replace('_0000.png', '.png')
        mask_file = mask_path / mask_name
        
        if mask_file.exists():
            img = iio.imread(img_file)
            mask = iio.imread(mask_file)
            yield img, mask, img_file.name
        else:
            print(f"Warning: Mask not found for {img_file.name}")


def refine_walls(lumen, walls):
    """
    Refine wall mask using Gaussian filtering and skeleton extraction.
    
    Args:
        lumen: Binary mask of vessel lumen (uint8 or bool)
        walls: Binary mask of vessel walls (uint8 or bool)
        
    Returns:
        Tuple of (refined_mask, skeleton)
            - refined_mask: Combined lumen (1) + refined walls (2)
            - skeleton: Skeleton of refined walls
    """
    lumen = lumen.astype(bool)
    walls = walls.astype(bool)
    
    # Gaussian filtering and thresholding
    mask2 = ndimage.gaussian_filter(walls.astype(float), sigma=3) > 0.5
    
    # Extract skeleton
    skel = morphology.skeletonize(mask2.astype(uint8 := np.uint8))
    
    # Label connected components in skeleton
    labeled_skel, num_features = label(skel)
    props = regionprops(labeled_skel, intensity_image=None)
    
    # Get area of each skeleton component
    areas = np.array([p.area for p in props])
    
    # Otsu threshold to remove small components
    if len(areas) > 0:
        # Normalize and compute threshold
        normalized_areas = areas / (areas.max() + 1e-7)
        level = np.mean(areas) * (np.min(normalized_areas) + 0.5 * (np.max(normalized_areas) - np.min(normalized_areas)))
        
        # Mark small components to remove
        mask3 = mask2.copy()
        for prop in props:
            if prop.area < level:
                mask3[labeled_skel == prop.label] = False
    else:
        mask3 = mask2.copy()
    
    # Clean skeleton with refined mask
    skel = skel * mask3.astype(np.uint8)
    
    # Create output mask: lumen (1) + walls (2)
    refined_mask = lumen.astype(np.uint8)
    refined_mask[mask3 & ~lumen] = 2
    
    return refined_mask, skel


def extract_skeleton(mask):
    """
    Extract and refine vessel skeleton with multi-scale processing.
    
    Args:
        mask: Binary vessel mask
        
    Returns:
        Labeled skeleton with connected components
    """
    mask = mask.astype(bool)
    
    # Downscale by 0.5
    mask1 = ndimage.zoom(mask.astype(float), 0.5, order=0) > 0.5
    
    # Pad with border extension
    h, w = mask1.shape
    pad_size = max(10, h // 10)
    mask2 = np.pad(mask1, pad_size, mode='edge')
    
    # Fill holes and remove small artifacts
    filled = ndimage.binary_fill_holes(mask2)
    objcts = filled & ~mask2
    labeled_objcts, _ = label(objcts)
    
    # Remove small objects
    props = regionprops(labeled_objcts)
    for prop in props:
        if prop.area > 50:
            objcts[labeled_objcts == prop.label] = False
    
    mask2 = mask2 | objcts
    
    # Morphological operations
    mask2 = ndimage.binary_erosion(mask2, structure=morphology.diamond(2))
    
    # Gaussian filtering
    mask3 = ndimage.gaussian_filter(mask2.astype(float), sigma=5) > 0.5
    mask4 = ndimage.gaussian_filter(mask3.astype(float), sigma=5) > 0.5
    mask2 = ndimage.binary_dilation(mask4, structure=morphology.diamond(2))
    
    # Extract skeleton
    # skel = skeletonize(mask2.astype(np.uint8), method='zhang')
    skel = medial_axis(mask2)

    # Crop back to original size and remove borders
    crop_size = pad_size
    skel = skel[crop_size:-crop_size, crop_size:-crop_size]
    
    # Remove edge pixels
    r = 3
    skel[:r+1, :] = False
    skel[-r:, :] = False
    skel[:, :r+1] = False
    skel[:, -r:] = False
    
    # Remove branch points (pixels with more than 2 neighbors in 8-connectivity)
    # MATLAB: skel = skel .* ~imdilate(bwmorph(skel,'branchpoints'),strel('disk',20))
    branch_kernel = np.array([[1, 1, 1],
                              [1, 0, 1],
                              [1, 1, 1]], dtype=np.uint8)
    neighbors = ndimage.convolve(skel.astype(np.uint8), branch_kernel, mode='constant', cval=0)
    branch_points = (skel > 0) & (neighbors > 2)  # Pixels with >2 neighbors are branch points
    
    # Dilate branch points by disk of radius 20 and remove from skeleton
    branchpts_dilated = ndimage.binary_dilation(branch_points, structure=morphology.disk(20))
    skel = skel & ~branchpts_dilated
    
    # Upscale back to original size BEFORE labeling (to keep skeleton thin)
    skel = ndimage.zoom(skel.astype(float), 2.0, order=0) > 0.5  # Convert back to binary
    skel = skel[:mask.shape[0], :mask.shape[1]]
    
    # Re-skeletonize after upscaling to remove thickening artifacts
    skel = medial_axis(skel)
    
    # Label connected components using 8-connectivity (diagonal connections matter for thin skeletons)
    structure_8conn = np.ones((3, 3), dtype=int)
    skel, _ = label(skel, structure=structure_8conn)
    
    return skel.astype(np.uint8)


def compute_normals(centerline, window_size=50, std_dev=1.0):
    """
    Compute unit normal vectors along centerline.
    EXACT port of MATLAB comp_normal.m function.
    
    Args:
        centerline: Nx2 array of (x, y) coordinates
        window_size: Size of Gaussian smoothing window (pad size) - param(1)
        std_dev: Gaussian shape parameter (MATLAB alpha) - param(2)
        
    Returns:
        Nx2 array of normal vectors (perpendicular to tangent)
    """
    if len(centerline) < 3:
        return np.zeros_like(centerline)
    
    # Create Gaussian window matching MATLAB gausswin(N, alpha)
    # MATLAB: gausswin(N, alpha) has std = N/(2*alpha) in the Gaussian exp
    # Convert to scipy gaussian which uses std directly
    std_converted = window_size / (2.0 * std_dev)
    win = gaussian(window_size, std=std_converted)
    win = win / np.sum(win)
    
    # Pad centerline: repeat first and last point window_size times
    # This matches MATLAB: cat(1, ones(param(1),2).*X(1,:), X, ones(param(1),2).*X(end,:))
    X = np.vstack([
        np.tile(centerline[0], (window_size, 1)),
        centerline,
        np.tile(centerline[-1], (window_size, 1))
    ])
    
    # Smooth with Gaussian convolution - apply to each column
    # MATLAB: X = conv2(X, win, 'same')
    X_smoothed = np.column_stack([
        np.convolve(X[:, 0], win, mode='same'),
        np.convolve(X[:, 1], win, mode='same')
    ])
    
    # Remove padding - keep only middle part
    # MATLAB: X = X(param(1)+1:end-param(1),:)
    # In Python (0-indexed): X[param(1):end-param(1)]
    X_smoothed = X_smoothed[window_size:-window_size, :]
    
    # Compute derivatives (tangent vectors)
    # MATLAB: dX = [X(2:end,:);X(end-1,:)] - [X(1:end,:)]
    # This means: dX(i) = X(i+1) - X(i), except dX(end) = X(end-1) - X(end)
    dX_forward = X_smoothed[1:] - X_smoothed[:-1]  # X(2:end) - X(1:end-1)
    dX_last = X_smoothed[-2:-1] - X_smoothed[-1:]   # X(end-1) - X(end)
    dX = np.vstack([dX_forward, dX_last])
    
    # Normalize to unit vectors
    vel = np.sqrt(dX[:, 0]**2 + dX[:, 1]**2)
    vel[vel == 0] = 1.0
    
    # Compute perpendicular (normal) vectors
    # MATLAB: nX = [dX(:,2), -dX(:,1)] ./ [vel, vel]
    normals = np.column_stack([
        dX[:, 1] / vel,
        -dX[:, 0] / vel
    ])
    
    return normals


def create_empty_measurement(vessel_id, pt):
    """
    Create an empty measurement dictionary with only central point.
    Used when profile fails to meet detection criteria.
    
    Args:
        vessel_id: Vessel ID number
        pt: Central point (x, y)
        
    Returns:
        Dictionary with all wall measurements as NaN
    """
    return {
        'Vessel': vessel_id,
        'Outer_X_left': np.nan,
        'Outer_Y_left': np.nan,
        'Inner_X_left': np.nan,
        'Inner_Y_left': np.nan,
        'Central_X': pt[0],
        'Central_Y': pt[1],
        'Inner_X_right': np.nan,
        'Inner_Y_right': np.nan,
        'Outer_X_right': np.nan,
        'Outer_Y_right': np.nan,
        'Wall_Left': np.nan,
        'Wall_Right': np.nan,
        'Lumen': np.nan,
        'WLR_Left': np.nan,
        'WLR_Right': np.nan
    }


def find_skeleton_endpoints(binary_skel: np.ndarray) -> np.ndarray:
    """
    Find endpoints (pixels with exactly one 8-connected neighbor) in a binary skeleton.
    Returns a boolean array mask with True at endpoints.
    """
    skel = (binary_skel > 0).astype(np.uint8)
    # 8-neighborhood kernel without center
    nbr_kernel = np.array([[1, 1, 1],
                           [1, 0, 1],
                           [1, 1, 1]], dtype=np.uint8)
    neighbors = ndimage.convolve(skel, nbr_kernel, mode='constant', cval=0)
    endpoints = (skel == 1) & (neighbors == 1)
    return endpoints


def order_centerline(binary_skel: np.ndarray):
    """
    Order skeleton pixels into a continuous polyline from one endpoint to the other.
    Assumes no branch points (they should be removed beforehand).
    Returns an Nx2 array of (x, y) coordinates. Returns None if empty.
    """
    skel = (binary_skel > 0)
    if not np.any(skel):
        return None

    # Find endpoints; if none, fall back to arbitrary start
    endpoints_mask = find_skeleton_endpoints(skel)
    ys, xs = np.where(endpoints_mask)
    if len(xs) == 0:
        ys, xs = np.where(skel)
        start = (ys[0], xs[0])
    else:
        start = (ys[0], xs[0])

    H, W = skel.shape
    visited = set()
    path = []
    y, x = start

    # 8-connected neighbor offsets
    neigh = [(-1, -1), (-1, 0), (-1, 1),
             (0, -1),           (0, 1),
             (1, -1),  (1, 0),  (1, 1)]

    while True:
        path.append([x, y])  # store as (x, y)
        visited.add((y, x))
        found_next = False
        for dy, dx in neigh:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and skel[ny, nx] and (ny, nx) not in visited:
                y, x = ny, nx
                found_next = True
                break
        if not found_next:
            break

    if len(path) == 0:
        return None
    return np.asarray(path, dtype=float)


def measure_vessel_walls(img, mask, skeleton, draw_profiles=True):
    """
    Measure vessel wall thickness along skeleton centerlines.
    
    Args:
        img: Original image
        mask: Refined vessel mask (1=lumen, 2=wall)
        skeleton: Labeled skeleton (vessel IDs)
        draw_profiles: If True, create overlay images with profile lines
        
    Returns:
        Tuple of (measurements_list, profile_overlay_image, wlr_overlay_image)
            - measurements_list: List of measurement dictionaries
            - profile_overlay_image: PIL Image with all profile normals (green and red)
            - wlr_overlay_image: PIL Image with only valid WLR profile lines (green only)
    """
    measurements = []
    
    # Create overlay images for profile visualization
    overlay_img = None
    wlr_overlay_img = None
    if draw_profiles:
        # Create visualization from mask: lumen=gray, wall=white, background=black, profiles=green
        mask_vis = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
        mask_vis[mask == 1] = [128, 128, 128]  # Lumen = gray
        mask_vis[mask == 2] = [255, 255, 255]  # Wall = white
        
        # Overlay for all profiles (green and red)
        overlay_img = Image.fromarray(mask_vis.copy(), 'RGB')
        draw = ImageDraw.Draw(overlay_img)
        
        # Overlay for only WLR measurements (green only)
        wlr_overlay_img = Image.fromarray(mask_vis.copy(), 'RGB')
        draw_wlr = ImageDraw.Draw(wlr_overlay_img)
    
    # Get unique vessel labels (skip 0 which is background)
    vessel_ids = np.unique(skeleton)
    vessel_ids = vessel_ids[vessel_ids > 0]
    
    for vessel_id in vessel_ids:
        vessel_skel = (skeleton == vessel_id).astype(np.uint8)
        
        # Find endpoints of skeleton (binary, single vessel)
        endpoints_mask = find_skeleton_endpoints(vessel_skel)
        y_pts, x_pts = np.where(endpoints_mask)
        if len(y_pts) == 0:
            continue

        # Build ordered centerline path from one endpoint to the other
        centerline = order_centerline(vessel_skel)
        if centerline is None or len(centerline) < 10:
            continue
        
        # Compute normals
        normals = compute_normals(centerline, window_size=30, std_dev=1.0)
        
        # Measure along profile lines
        wall_measurements = []
        line_length = 200
        
        for k in range(30, len(centerline) - 30, 2):
            pt = centerline[k]
            normal = normals[k]
            
            # Create profile line endpoints
            p1 = pt - normal * line_length
            p2 = pt + normal * line_length
            
            # Clamp to image bounds for drawing
            # p1_clamped = np.clip(p1, 0, [img.shape[1]-1, img.shape[0]-1])
            # p2_clamped = np.clip(p2, 0, [img.shape[1]-1, img.shape[0]-1])
            p1_clamped = p1.copy()
            p2_clamped = p2.copy()
            
            # Sample intensity profile along line (400 points)
            profile_x = np.linspace(p1[0], p2[0], 400)
            profile_y = np.linspace(p1[1], p2[1], 400)
            
            # Get mask values along profile (1=lumen, 2=wall, 0=background)
            wall = ndimage.map_coordinates(
                mask.astype(float),
                [profile_y, profile_x],
                order=1,
                cval=0
            )
            
            # Split profile at centerline
            mid = len(wall) // 2
            W1 = wall[:mid]                # left half
            W2 = wall[mid:]                # right half
            
            # Check if there are enough background pixels (0) on both sides
            # MATLAB: if ( (length(find(W1==0))>5) & (length(find(W2==0))>5) )
            if not (np.count_nonzero(W1 == 0) > 5 and np.count_nonzero(W2 == 0) > 5):
                # Insufficient background on one or both sides - skip this profile but save central point
                if draw_profiles and k % 3 == 0:
                    # Still visualize the attempted perpendicular (red = invalid measurement)
                    draw.line(
                        [(p1_clamped[0], p1_clamped[1]), (p2_clamped[0], p2_clamped[1])],
                        fill=(255, 165, 0),  # Orange
                        width=2
                    )
                wall_measurements.append(create_empty_measurement(vessel_id, pt))
                continue
            
            # Find outer boundaries (last zero on left, first zero on right)
            # MATLAB: p01 = find(W1==0,1,'last'); p02 = find(W2==0,1,'first');
            zeros_left = np.where(W1 == 0)[0]
            zeros_right = np.where(W2 == 0)[0]
            
            p01 = zeros_left[-1] if len(zeros_left) > 0 else None  # last zero on left
            p02 = zeros_right[0] if len(zeros_right) > 0 else None  # first zero on right
            
            # Trim profiles to remove background outside walls
            # MATLAB: W1(1:p01)=0; W2(p02:end)=0;
            if p01 is not None:
                W1 = W1[p01:]
            if p02 is not None:
                W2 = W2[:p02]
            
            # Find wall boundaries (first wall=2 on left, last wall=2 on right)
            # MATLAB: p1 = find(W1==2,1,'first'); p4 = find(W2==2,1,'last');
            wall_2_left = np.where(W1 == 2)[0]
            wall_2_right = np.where(W2 == 2)[0]
            
            p1 = wall_2_left[0] if len(wall_2_left) > 0 else None      # first wall on left (outer_left)
            p4 = wall_2_right[-1] if len(wall_2_right) > 0 else None   # last wall on right (outer_right)
            
            # Find lumen boundaries (first lumen=1 on left, last lumen=1 on right)
            # MATLAB: p2 = find(W1==1,1,'first'); p3 = find(W2==1,1,'last')+(length(wall)/2);
            lumen_1_left = np.where(W1 == 1)[0]
            lumen_1_right = np.where(W2 == 1)[0]
            
            p2 = lumen_1_left[0] if len(lumen_1_left) > 0 else None    # first lumen on left (inner_left)
            p3 = lumen_1_right[-1] if len(lumen_1_right) > 0 else None # last lumen on right (inner_right)
            
            # Convert MATLAB profile indices back to original profile coordinates
            # MATLAB indices are in trimmed arrays, need to map back
            if p01 is not None:
                p1_orig = (p01 + p1) if p1 is not None else None
                p2_orig = (p01 + p2) if p2 is not None else None
            else:
                p1_orig = p1
                p2_orig = p2
            
            # Right side indices are already trimmed to length p02, so map directly to the original profile start at 'mid'
            p3_orig = (mid + p3) if p3 is not None else None
            p4_orig = (mid + p4) if p4 is not None else None
            
            # Get actual profile indices for outer boundaries (in original profile)
            p01_orig = p01
            p02_orig = mid + p02 if p02 is not None else None
            
            # Extract coordinates from profile
            central_x = pt[0]
            central_y = pt[1]
            
            # Outer left (position of outer wall on left)
            outer_x_left = profile_x[p1_orig] if p1_orig is not None else np.nan
            outer_y_left = profile_y[p1_orig] if p1_orig is not None else np.nan
            
            # Inner left (position of lumen on left)
            inner_x_left = profile_x[p2_orig] if p2_orig is not None else np.nan
            inner_y_left = profile_y[p2_orig] if p2_orig is not None else np.nan
            
            # Inner right (position of lumen on right)
            inner_x_right = profile_x[p3_orig] if p3_orig is not None else np.nan
            inner_y_right = profile_y[p3_orig] if p3_orig is not None else np.nan
            
            # Outer right (position of outer wall on right)
            outer_x_right = profile_x[p4_orig] if p4_orig is not None else np.nan
            outer_y_right = profile_y[p4_orig] if p4_orig is not None else np.nan
            
            # Check if we have any wall detection on at least one side; if not, skip
            if np.isnan(outer_x_left) and np.isnan(outer_x_right):
                # No wall on either side - only store central point
                if draw_profiles and k % 3 == 0:
                    # Visualize attempted perpendicular even when no wall found
                    draw.line(
                        [(p1_clamped[0], p1_clamped[1]), (p2_clamped[0], p2_clamped[1])],
                        fill=(255, 165, 0),  # Orange
                        width=2
                    )
                wall_measurements.append(create_empty_measurement(vessel_id, pt))
                continue
            
            # Compute wall thickness as Euclidean distance (MATLAB)
            # Wall_Left = sqrt((outer_x_left - inner_x_left)^2 + (outer_y_left - inner_y_left)^2)
            if not np.isnan(outer_x_left) and not np.isnan(inner_x_left):
                wall_left_thickness = np.sqrt((outer_x_left - inner_x_left)**2 + (outer_y_left - inner_y_left)**2)
            else:
                wall_left_thickness = np.nan
            
            # Wall_Right = sqrt((inner_x_right - outer_x_right)^2 + (inner_y_right - outer_y_right)^2)
            if not np.isnan(outer_x_right) and not np.isnan(inner_x_right):
                wall_right_thickness = np.sqrt((inner_x_right - outer_x_right)**2 + (inner_y_right - outer_y_right)**2)
            else:
                wall_right_thickness = np.nan
            
            # Compute lumen diameter as distance between outer walls
            # MATLAB logic: try outer_left to outer_right first, then fallback
            # Lumen = sqrt((outer_x_left - outer_x_right)^2 + (outer_y_left - outer_y_right)^2)
            if not np.isnan(outer_x_left) and not np.isnan(outer_x_right):
                lumen_diameter = np.sqrt((outer_x_left - outer_x_right)**2 + (outer_y_left - outer_y_right)**2)
            elif not np.isnan(outer_x_left):
                # Fallback: 2x distance from outer_left to center
                lumen_diameter = 2 * np.sqrt((outer_x_left - central_x)**2 + (outer_y_left - central_y)**2)
            elif not np.isnan(outer_x_right):
                # Fallback: 2x distance from outer_right to center
                lumen_diameter = 2 * np.sqrt((outer_x_right - central_x)**2 + (outer_y_right - central_y)**2)
            else:
                lumen_diameter = np.nan
            
            # Compute WLR (wall-to-lumen ratio) - only for sides with wall detection
            if not np.isnan(wall_left_thickness) and not np.isnan(lumen_diameter) and lumen_diameter > 0:
                wlr_left = wall_left_thickness / lumen_diameter
            else:
                wlr_left = np.nan
            
            if not np.isnan(wall_right_thickness) and not np.isnan(lumen_diameter) and lumen_diameter > 0:
                wlr_right = wall_right_thickness / lumen_diameter
            else:
                wlr_right = np.nan
            
            wall_measurements.append({
                'Vessel': vessel_id,
                'Outer_X_left': outer_x_left,
                'Outer_Y_left': outer_y_left,
                'Inner_X_left': inner_x_left,
                'Inner_Y_left': inner_y_left,
                'Central_X': central_x,
                'Central_Y': central_y,
                'Inner_X_right': inner_x_right,
                'Inner_Y_right': inner_y_right,
                'Outer_X_right': outer_x_right,
                'Outer_Y_right': outer_y_right,
                'Wall_Left': wall_left_thickness,
                'Wall_Right': wall_right_thickness,
                'Lumen': lumen_diameter,
                'WLR_Left': wlr_left,
                'WLR_Right': wlr_right
            })
            
            # Draw profile line on overlays (green = valid measurement)
            if draw_profiles and k % 3 == 0:
                # All-profiles overlay: draw every attempted perpendicular (green = valid)
                draw.line(
                    [(p1_clamped[0], p1_clamped[1]), (p2_clamped[0], p2_clamped[1])],
                    fill=(0, 255, 0),  # Green
                    width=2
                )
                # WLR overlay: show inner or outer depending on wall measurement
                if np.isnan(outer_x_left) and np.isnan(outer_x_right):
                    draw_wlr.line(
                        [(inner_x_left, inner_y_left), (inner_x_right, inner_y_right)],
                        fill=(0, 255, 0),  # Green
                        width=2
                    )
                elif np.isnan(outer_x_left):
                    draw_wlr.line(
                        [(inner_x_left, inner_y_left), (outer_x_right, outer_y_right)],
                        fill=(0, 255, 0),  # Green
                        width=2
                    )
                elif np.isnan(outer_x_right):
                    draw_wlr.line(
                        [(outer_x_left, outer_y_left), (inner_x_right, inner_y_right)],
                        fill=(0, 255, 0),  # Green
                        width=2
                    )
                else:
                    draw_wlr.line(
                        [(outer_x_left, outer_y_left), (outer_x_right, outer_y_right)],
                        fill=(0, 255, 0),  # Green
                        width=2
                    )
        
        measurements.extend(wall_measurements)
    
    return measurements, overlay_img, wlr_overlay_img

def create_labeled_mask_from_skeleton(mask, skeleton):
    """
    Create labeled mask where each pixel is labeled by nearest skeleton segment.
    
    Port of MATLAB code:
        pom = double(mask>0); pom(pom==0) = -inf; pom(pom==1) = inf;
        DM=[]; DM(:,:,1) = pom;
        for ves = 1:max(skel,[],'all')
            DM(:,:,ves+1) = bwdist((skel==ves));
        end
        [lbl_ves, ind] = min(DM,[],3);
        ind = ind-1;
    
    Args:
        mask: Binary mask (1=vessel, 0=background)
        skeleton: Labeled skeleton with vessel IDs (1,2,3,...)
        
    Returns:
        Labeled mask where each pixel is labeled by nearest skeleton segment ID
    """
    from scipy.ndimage import distance_transform_edt
    
    H, W = mask.shape
    
    # Create initial distance map layer
    # Background: -inf, Vessel: +inf
    pom = np.full((H, W), -np.inf, dtype=float)
    pom[mask > 0] = np.inf
    
    # Get unique skeleton IDs
    skeleton_ids = np.unique(skeleton)
    skeleton_ids = skeleton_ids[skeleton_ids > 0]
    
    # Create 3D distance matrix
    # Layer 0: pom (background=-inf, vessel=+inf)
    # Layers 1+: distance from each skeleton segment
    DM = np.zeros((H, W, len(skeleton_ids) + 1), dtype=float)
    DM[:, :, 0] = pom
    
    # For each skeleton segment, compute Euclidean distance
    for idx, ves_id in enumerate(skeleton_ids, start=1):
        skeleton_mask = (skeleton == ves_id)
        if np.any(skeleton_mask):
            # Distance transform: distance from pixels where skeleton == ves_id
            DM[:, :, idx] = distance_transform_edt(~skeleton_mask)
        else:
            DM[:, :, idx] = np.inf
    
    # Find argmin along 3rd dimension (returns which layer has minimum)
    labeled_mask = np.argmin(DM, axis=2)  # 0-based in Python
    
    return labeled_mask.astype(np.uint8)


def save_results(measurements, output_dir, filename_base, img, mask, skeleton, profile_overlay=None, wlr_overlay=None):
    """
    Save analysis results as PNG images and XLSX table.
    
    Args:
        measurements: List of measurement dictionaries
        output_dir: Directory to save results
        filename_base: Base filename (without extension)
        img: Original image
        mask: Refined mask
        skeleton: Labeled skeleton
        profile_overlay: PIL Image with all drawn profile lines (optional)
        wlr_overlay: PIL Image with only WLR profile lines (optional)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save original image
    img_uint8 = np.clip(img / img.max() * 255, 0, 255).astype(np.uint8) if img.max() > 0 else img.astype(np.uint8)
    iio.imwrite(output_path / f"{filename_base}_orig.png", img_uint8)
    
    # Save segmentation mask
    mask_vis = (mask * 120).astype(np.uint8)
    iio.imwrite(output_path / f"{filename_base}_pred.png", mask_vis)
    
    # Save labeled vessel mask
    labeled_mask = create_labeled_mask_from_skeleton(mask, skeleton)
    labeled_mask[skeleton > 0] = 0
    labeled_mask = (labeled_mask / labeled_mask.max() * 255).astype(np.uint8) if labeled_mask.max() > 0 else labeled_mask.astype(np.uint8)
    
    iio.imwrite(output_path / f"{filename_base}_labels_vessels.png", labeled_mask)
    
    # Save profile overlay if available (all profiles - green and red)
    if profile_overlay is not None:
        profile_overlay.save(output_path / f"{filename_base}_profiles.png")
    
    # Save WLR overlay if available (only valid WLR measurements - green only)
    if wlr_overlay is not None:
        wlr_overlay.save(output_path / f"{filename_base}_profiles_wlr.png")
    
    # Save measurements as Excel
    if measurements:
        df = pd.DataFrame(measurements)
        # Reorder columns to match MATLAB output
        column_order = [
            'Vessel', 'Outer_X_left', 'Outer_Y_left', 'Inner_X_left', 'Inner_Y_left',
            'Central_X', 'Central_Y', 'Inner_X_right', 'Inner_Y_right', 'Outer_X_right', 'Outer_Y_right',
            'Wall_Left', 'Wall_Right', 'Lumen', 'WLR_Left', 'WLR_Right'
        ]
        df = df[column_order]
        
        # Remove rows where all wall measurements are NaN (only central point exists)
        wall_cols = ['Outer_X_left', 'Outer_Y_left', 'Inner_X_left', 'Inner_Y_left', 
                     'Inner_X_right', 'Inner_Y_right', 'Outer_X_right', 'Outer_Y_right']
        df_filtered = df[~df[wall_cols].isna().all(axis=1)]
        
        # Replace NaN with -1 (MATLAB convention)
        df_filtered = df_filtered.fillna(-1)
        
        df_filtered.to_excel(output_path / f"{filename_base}.xlsx", index=False)
    else:
        # Create empty DataFrame with expected columns
        df = pd.DataFrame(columns=[
            'Vessel', 'Outer_X_left', 'Outer_Y_left', 'Inner_X_left', 'Inner_Y_left',
            'Central_X', 'Central_Y', 'Inner_X_right', 'Inner_Y_right', 'Outer_X_right', 'Outer_Y_right',
            'Wall_Left', 'Wall_Right', 'Lumen', 'WLR_Left', 'WLR_Right'
        ])
        df.to_excel(output_path / f"{filename_base}.xlsx", index=False)


if __name__ == "__main__":
    # Test module imports
    print("Vessel analysis module loaded successfully")
