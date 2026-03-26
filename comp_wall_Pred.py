#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main script for vessel wall analysis on retinal AO images.
Processes all images in input directory and saves results as PNG + XLSX.
"""

import argparse
from pathlib import Path
import sys
from vessel_analysis import (
    load_images, refine_walls, extract_skeleton, 
    measure_vessel_walls, save_results
)





def process_images(path_data, path_masks, path_save, verbose=False):
    """
    Process all images and compute vessel wall measurements.
    
    Args:
        path_data: Directory with original images
        path_masks: Directory with segmentation masks
        path_save: Directory to save results
        verbose: Print progress information
    """
    path_save = Path(path_save)
    path_save.mkdir(parents=True, exist_ok=True)
    
    total_images = len(list(Path(path_data).glob('*.png')))
    print(f"Found {total_images} images")
    
    processed_count = 0
    success_count = 0
    
    for idx, (img, mask, filename) in enumerate(load_images(path_data, path_masks), 1):
        try:
            filename_base = filename.replace('_0000.png', '').replace('.png', '')
            
            if verbose:
                print(f"\n[{idx}/{total_images}] Processing: {filename}")
            else:
                print(
                    f"\r[{idx:>5}/{total_images:<5}] ok:{success_count:<4} err:{(processed_count - success_count):<4}",
                    end='',
                    flush=True
                )
            
            # Parse mask: 126=lumen, 252=walls (based on comp_wall_Pred.m)
            lumen = (mask == 126).astype('uint8')
            walls = (mask == 252).astype('uint8')
            
            # Refine walls and extract skeleton
            refined_mask, wall_skeleton = refine_walls(lumen, walls)
            vessel_skeleton = extract_skeleton(lumen)
            
            # import matplotlib.pyplot as plt

            # fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            # axes[0].imshow(refined_mask, cmap='gray')
            # axes[0].set_title('Refined Mask')
            # axes[0].axis('off')
            # axes[1].imshow(vessel_skeleton, cmap='gray')
            # axes[1].set_title('Wall Skeleton')
            # axes[1].axis('off')
            # plt.tight_layout()
            # plt.show()

            # Measure vessel walls
            measurements, profile_overlay, wlr_overlay = measure_vessel_walls(img, refined_mask, vessel_skeleton)
            
            # Save results
            save_results(
                measurements,
                path_save,
                filename_base,
                img,
                refined_mask,
                vessel_skeleton,
                profile_overlay,
                wlr_overlay
            )
            
            success_count += 1
            
        except Exception as e:
            if verbose:
                print(f"  ERROR: {str(e)}")
            else:
                print(f"\n  ERROR in {filename}: {str(e)}")
        finally:
            processed_count += 1
    
    print(f"\n\nProcessing complete!")
    print(f"  Processed: {processed_count}/{total_images}")
    print(f"  Successful: {success_count}/{total_images}")
    print(f"  Results saved to: {path_save}")


def main():
    # Debug mode: use hardcoded paths if no arguments provided (for VS Code debugger)
    import sys
    if len(sys.argv) == 1:
        print("No arguments provided. Running in DEBUG mode with default paths...")
        print()
        
        # Default paths for debugging
        path_images = r'C:\Data\Jakubicek\AO_retinal\Data\Tested_data_12_2025\images'
        path_masks = r'C:\Data\Jakubicek\AO_retinal\Data\Tested_data_12_2025\masks'
        path_output = r'C:\Data\Jakubicek\AO_retinal\Data\Tested_data_12_2025\results_analysis'
        verbose = True
        
        print(f"Images:  {path_images}")
        print(f"Masks:   {path_masks}")
        print(f"Output:  {path_output}")
        print(f"Verbose: {verbose}")
        print()
        
        if not Path(path_images).exists():
            print(f"ERROR: Images directory not found: {path_images}")
            sys.exit(1)
        
        if not Path(path_masks).exists():
            print(f"ERROR: Masks directory not found: {path_masks}")
            sys.exit(1)
        
        process_images(path_images, path_masks, path_output, verbose=verbose)
    else:
        # Command-line mode: parse arguments
        parser = argparse.ArgumentParser(
            description="Analyze vessel walls in retinal AO images"
        )
        parser.add_argument(
            '-i', '--images',
            required=True,
            help="Directory with input PNG images"
        )
        parser.add_argument(
            '-m', '--masks',
            required=True,
            help="Directory with segmentation masks"
        )
        parser.add_argument(
            '-o', '--output',
            required=True,
            help="Directory to save results"
        )
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help="Print detailed progress information"
        )
        
        args = parser.parse_args()
        
        # Validate input directories
        if not Path(args.images).exists():
            print(f"ERROR: Images directory not found: {args.images}")
            sys.exit(1)
        
        if not Path(args.masks).exists():
            print(f"ERROR: Masks directory not found: {args.masks}")
            sys.exit(1)
        
        process_images(args.images, args.masks, args.output, verbose=args.verbose)


if __name__ == "__main__":
    main()
