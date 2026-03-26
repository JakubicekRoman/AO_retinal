#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive WLR analysis database: quality metrics, reliability, and population statistics.
Analyzes:
1. Vessels_ALL - Large dataset with population statistics
2. Stack - Intra-observer reliability (multiple focii of same location)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re
from scipy import stats
from PIL import Image, ImageDraw


def parse_filename_metadata(filename):
    """
    Extract metadata from Excel filename.
    Format: OD_20250713103754_X14.2N_Y8.4_Z130.0_ERHARDT_Christine_LS056_EC.xlsx
           OS_20251201163655_X12.0N_Y-4.3_Z130.0_FRANCKE_Mike.xlsx
    Returns: dict with date, coordinates, patient_name
    """
    # Remove extension
    base_name = filename.replace('.xlsx', '')
    
    result = {
        'filename': filename,
        'eye': None,
        'date_str': None,
        'date': None,
        'x_coord': None,
        'y_coord': None,
        'z_coord': None,
        'patient_name': None,
        'patient_id': None,
    }
    
    # Parse using regex patterns
    # Pattern for X coordinate: X followed by number and N/S
    x_match = re.search(r'X([\d.]+)[NS]', base_name)
    if x_match:
        result['x_coord'] = float(x_match.group(1))
    
    # Pattern for Y coordinate: Y followed by number (can be negative), ends with underscore or Z
    y_match = re.search(r'Y([-\d.]+)(?=_|Z)', base_name)
    if y_match:
        result['y_coord'] = float(y_match.group(1))
    
    # Pattern for Z coordinate: Z followed by number, ends with underscore or end of string
    z_match = re.search(r'Z([\d.]+)(?=_|$)', base_name)
    if z_match:
        result['z_coord'] = float(z_match.group(1))
    
    # Extract eye (OD/OS)
    parts = base_name.split('_')
    if parts[0] in ['OD', 'OS']:
        result['eye'] = parts[0]
    
    # Extract date
    if len(parts) > 1:
        result['date_str'] = parts[1]
        try:
            result['date'] = datetime.strptime(result['date_str'], '%Y%m%d%H%M%S')
        except:
            pass
    
    # Extract patient name (everything after Z coordinate until .xlsx or LS)
    # Format: Z[number]_PatientName[_Optional_Number][_LS_ID][_Other].xlsx
    # Examples: Z210.0_WALLSTABE_Kristin or Z130.0_PIECHNICK_Janne_037 or Z100.0_ERHARDT_Christine_LS056
    
    # Check for LS ID
    ls_match = re.search(r'LS\d+', base_name)
    if ls_match:
        result['patient_id'] = ls_match.group()
    
    # Extract patient name - just take first 2 underscore-separated parts after Z
    # Format is always: Z[number]_LASTNAME_FIRSTNAME[_optional_suffix]
    z_match = re.search(r'Z[\d.]+_(.+?)(?:_LS\d+|$)', base_name)
    if z_match:
        after_z = z_match.group(1)
        parts = after_z.split('_')
        # Take first 2 parts: LASTNAME and FIRSTNAME
        if len(parts) >= 2:
            result['patient_name'] = f"{parts[0]} {parts[1]}"
        else:
            result['patient_name'] = parts[0]
    
    return result


def load_and_analyze_excel(filepath):
    """Load Excel file and extract WLR statistics."""
    try:
        df = pd.read_excel(filepath)
        
        # Extract valid WLR values (exclude -1 which is NaN marker)
        wlr_values = []
        
        if 'WLR_Left' in df.columns:
            wlr_left = df['WLR_Left'].values
            wlr_left = wlr_left[wlr_left >= 0]
            wlr_values.extend(wlr_left)
        
        if 'WLR_Right' in df.columns:
            wlr_right = df['WLR_Right'].values
            wlr_right = wlr_right[wlr_right >= 0]
            wlr_values.extend(wlr_right)
        
        wlr_values = np.array(wlr_values)
        
        if len(wlr_values) > 0:
            return {
                'n_measurements': len(wlr_values),
                'mean_wlr': np.mean(wlr_values),
                'std_wlr': np.std(wlr_values),
                'median_wlr': np.median(wlr_values),
                'min_wlr': np.min(wlr_values),
                'max_wlr': np.max(wlr_values),
                'q1_wlr': np.percentile(wlr_values, 25),
                'q3_wlr': np.percentile(wlr_values, 75),
                'wlr_values': wlr_values,
                'n_rows': len(df),
                'success_rate': len(wlr_values) / (len(df) * 2) * 100  # 2 sides per profile
            }
        else:
            return None
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def analyze_vessels_all(data_dir):
    """Analyze Vessels_ALL large database."""
    print("\n" + "="*80)
    print("ANALYSIS: Vessels_ALL Database")
    print("="*80)
    
    results_dir = Path(data_dir) / "results"
    
    if not results_dir.exists():
        print(f"Directory not found: {results_dir}")
        return None
    
    # Load all Excel files
    all_data = []
    
    for xlsx_file in sorted(results_dir.glob('*.xlsx')):
        metadata = parse_filename_metadata(xlsx_file.name)
        stats = load_and_analyze_excel(xlsx_file)
        
        if stats:
            record = {
                **metadata,
                **stats
            }
            all_data.append(record)
    
    if not all_data:
        print("No valid measurements found")
        return None
    
    df_all = pd.DataFrame(all_data)
    
    # Print statistics
    print(f"\nDataset size: {len(df_all)} images")
    print(f"Date range: {df_all['date'].min()} to {df_all['date'].max()}")
    
    # Unique patients
    unique_patients = df_all['patient_name'].nunique()
    unique_eyes = df_all['eye'].nunique()
    print(f"Unique patients: {unique_patients}")
    print(f"Unique eyes: {unique_eyes}")
    
    # WLR Statistics
    all_wlr = np.concatenate(df_all['wlr_values'].values)
    print(f"\nGlobal WLR Statistics (n={len(all_wlr)}):")
    print(f"  Mean:     {np.mean(all_wlr):.4f} ± {np.std(all_wlr):.4f}")
    print(f"  Median:   {np.median(all_wlr):.4f}")
    print(f"  Range:    [{np.min(all_wlr):.4f}, {np.max(all_wlr):.4f}]")
    print(f"  Q1-Q3:    {np.percentile(all_wlr, 25):.4f} - {np.percentile(all_wlr, 75):.4f}")
    
    # Measurement quality
    print(f"\nMeasurement Quality:")
    print(f"  Avg measurements per image: {df_all['n_measurements'].mean():.1f} ± {df_all['n_measurements'].std():.1f}")
    print(f"  Avg success rate: {df_all['success_rate'].mean():.1f}% ± {df_all['success_rate'].std():.1f}%")
    
    # Per-patient statistics
    print(f"\nPer-Patient Statistics:")
    patient_stats = df_all.groupby('patient_name').agg({
        'mean_wlr': ['count', 'mean', 'std'],
        'n_measurements': 'mean'
    }).round(4)
    print(patient_stats)
    
    # Detect outliers
    print(f"\nOutlier Detection (images with unusual WLR):")
    mean_all = df_all['mean_wlr'].mean()
    std_all = df_all['mean_wlr'].std()
    threshold_low = mean_all - 2*std_all
    threshold_high = mean_all + 2*std_all
    
    outliers = df_all[(df_all['mean_wlr'] < threshold_low) | (df_all['mean_wlr'] > threshold_high)]
    print(f"  Outliers (mean ± 2σ): {len(outliers)} / {len(df_all)}")
    
    if len(outliers) > 0:
        print("\n  Outlier images:")
        for idx, row in outliers.iterrows():
            print(f"    {row['filename']}: WLR={row['mean_wlr']:.4f}")
    
    return df_all, all_wlr


def analyze_stack(data_dir):
    """Analyze Stack intra-observer reliability."""
    print("\n" + "="*80)
    print("ANALYSIS: Stack Data (Intra-observer Reliability)")
    print("="*80)
    
    results_dir = Path(data_dir) / "results_WLR"
    
    if not results_dir.exists():
        print(f"Directory not found: {results_dir}")
        return None
    
    # Group by location (same patient, same coordinates, different focus)
    all_data = []
    
    # Recursively find all Excel files in nested directory structure
    for xlsx_file in sorted(results_dir.rglob('*.xlsx')):
        # Skip non-measurement files (those with suffixes like _labels_vessels, _profiles, etc.)
        if any(suffix in xlsx_file.name for suffix in ['_labels', '_orig', '_pred', '_profiles', '_measuring']):
            continue
        
        metadata = parse_filename_metadata(xlsx_file.name)
        stats = load_and_analyze_excel(xlsx_file)
        
        if stats:
            record = {
                **metadata,
                **stats
            }
            all_data.append(record)
    
    if not all_data:
        print("No valid measurements found")
        return None
    
    df_stack = pd.DataFrame(all_data)
    
    print(f"\nDataset size: {len(df_stack)} images")
    print(f"Date range: {df_stack['date'].min()} to {df_stack['date'].max()}")
    
    # Filter out rows with missing coordinates (patient_name optional)
    df_valid = df_stack.dropna(subset=['x_coord', 'y_coord', 'z_coord'])
    
    if len(df_valid) == 0:
        print("\n[WARNING] No valid coordinates found in filenames!")
        print("Sample filenames:")
        for fname in df_stack['filename'].head(3):
            print(f"  {fname}")
        return None
    
    print(f"Valid coordinates: {len(df_valid)} / {len(df_stack)} images")
    
    # DEBUG: Show sample parsed data
    print(f"\nSample parsed metadata:")
    for i in range(min(3, len(df_valid))):
        row = df_valid.iloc[i]
        print(f"  {row['filename']}")
        print(f"    Patient: {row['patient_name']}, X={row['x_coord']:.1f}, Y={row['y_coord']:.1f}, Z={row['z_coord']:.1f}")
    
    # Group by location (same patient, same X,Y coordinates, different Z focus levels)
    # Z coordinate represents the focus/depth level
    df_valid['location_key'] = (df_valid['patient_name'].astype(str) + '_' + 
                                 df_valid['x_coord'].round(1).astype(str) + '_' + 
                                 df_valid['y_coord'].round(1).astype(str))
    
    location_groups = df_valid.groupby('location_key')
    
    print(f"\nUnique locations (X,Y): {len(location_groups)}")
    print(f"  Total images with valid coords: {len(df_valid)}")
    
    # Count locations by number of focus levels
    group_sizes = location_groups.size()
    print(f"\nFocus level distribution:")
    print(f"  Locations with 1 image:   {(group_sizes == 1).sum()}")
    print(f"  Locations with 2 images:  {(group_sizes == 2).sum()}")
    print(f"  Locations with 3+ images: {(group_sizes >= 3).sum()}")
    print(f"  Max focus levels per location: {group_sizes.max()}")
    
    # Show sample locations with multiple focus levels
    multi_focus = group_sizes[group_sizes >= 2]
    if len(multi_focus) > 0:
        print(f"\nSample locations with multiple focus levels:")
        for i, (loc_key, count) in enumerate(multi_focus.head(5).items()):
            group = df_valid[df_valid['location_key'] == loc_key]
            print(f"  {i+1}. {loc_key}: {count} focus levels")
            print(f"     Z range: {group['z_coord'].min():.0f} - {group['z_coord'].max():.0f}")
            print(f"     WLR: {group['mean_wlr'].mean():.4f} ± {group['mean_wlr'].std():.4f}")
    
    # Calculate ICC for locations with multiple measurements
    reliability_results = []
    
    for location_key, group in location_groups:
        if len(group) >= 2:  # At least 2 focus levels
            wlr_values = group['mean_wlr'].values
            z_values = group['z_coord'].values
            
            # Calculate variability across focus levels
            reliability_results.append({
                'location': location_key,
                'patient': group['patient_name'].iloc[0],
                'x_coord': group['x_coord'].iloc[0],
                'y_coord': group['y_coord'].iloc[0],
                'n_focus_levels': len(group),
                'z_min': np.min(z_values),
                'z_max': np.max(z_values),
                'z_range': np.max(z_values) - np.min(z_values),
                'mean_wlr': np.mean(wlr_values),
                'std_wlr': np.std(wlr_values),
                'range_wlr': np.max(wlr_values) - np.min(wlr_values),
                'wlr_values': wlr_values,
                'z_values': z_values
            })
    
    if reliability_results:
        df_reliability = pd.DataFrame(reliability_results)
        
        print(f"\n{'='*80}")
        print(f"Reliability Analysis (Intra-observer variability at different focus levels)")
        print(f"{'='*80}")
        print(f"\nLocations with repeated measurements: {len(df_reliability)}")
        print(f"\nVariability across focus levels:")
        print(f"  Avg std per location: {df_reliability['std_wlr'].mean():.4f} ± {df_reliability['std_wlr'].std():.4f}")
        print(f"  Avg range per location: {df_reliability['range_wlr'].mean():.4f}")
        print(f"  Max std per location: {df_reliability['std_wlr'].max():.4f}")
        
        # Find most stable and least stable locations
        most_stable = df_reliability.loc[df_reliability['std_wlr'].idxmin()]
        least_stable = df_reliability.loc[df_reliability['std_wlr'].idxmax()]
        
        print(f"\nMost stable location:")
        print(f"  Patient: {most_stable['patient']}, X={most_stable['x_coord']:.1f}, Y={most_stable['y_coord']:.1f}")
        print(f"  Focus range: Z={most_stable['z_min']:.0f} to {most_stable['z_max']:.0f}")
        print(f"  WLR stability: {most_stable['std_wlr']:.4f}")
        
        print(f"\nLeast stable location:")
        print(f"  Patient: {least_stable['patient']}, X={least_stable['x_coord']:.1f}, Y={least_stable['y_coord']:.1f}")
        print(f"  Focus range: Z={least_stable['z_min']:.0f} to {least_stable['z_max']:.0f}")
        print(f"  WLR variability: {least_stable['std_wlr']:.4f}")
        
        # Calculate global WLR stats
        all_wlr_stack = np.concatenate(df_stack['wlr_values'].values)
        print(f"\nGlobal WLR Statistics (n={len(all_wlr_stack)}):")
        print(f"  Mean: {np.mean(all_wlr_stack):.4f} ± {np.std(all_wlr_stack):.4f}")
        print(f"  Median: {np.median(all_wlr_stack):.4f}")
        print(f"  Range: [{np.min(all_wlr_stack):.4f}, {np.max(all_wlr_stack):.4f}]")
        
        return df_valid, df_reliability
    else:
        print("\n[WARNING] No locations with repeated measurements found")
        all_wlr_stack = np.concatenate(df_valid['wlr_values'].values)
        print(f"\nGlobal WLR Statistics (n={len(all_wlr_stack)}):")
        print(f"  Mean: {np.mean(all_wlr_stack):.4f} ± {np.std(all_wlr_stack):.4f}")
        return df_valid, None


def create_vessels_all_plots(df_all, all_wlr, output_dir):
    """Create visualizations for Vessels_ALL analysis."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    sns.set_style("whitegrid")
    
    # 1. Distribution of WLR
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(all_wlr, bins=50, color='steelblue', alpha=0.7, edgecolor='black')
    ax.axvline(np.mean(all_wlr), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(all_wlr):.4f}')
    ax.axvline(np.median(all_wlr), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(all_wlr):.4f}')
    ax.set_xlabel('WLR (Wall-to-Lumen Ratio)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('WLR Distribution - Vessels_ALL Database', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_path / 'WLR_Distribution.png', dpi=150, bbox_inches='tight')
    print(f"[OK] Saved: WLR_Distribution.png")
    plt.close()
    
    # 2. Per-image mean WLR
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(range(len(df_all)), df_all['mean_wlr'].values, color='steelblue', alpha=0.7, edgecolor='black')
    ax.axhline(df_all['mean_wlr'].mean(), color='red', linestyle='--', linewidth=2, label='Global mean')
    ax.set_xlabel('Image', fontsize=12)
    ax.set_ylabel('Mean WLR', fontsize=12)
    ax.set_title('Mean WLR per Image', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_path / 'WLR_PerImage.png', dpi=150, bbox_inches='tight')
    print(f"[OK] Saved: WLR_PerImage.png")
    plt.close()
    
    # 3. Per-patient comparison
    fig, ax = plt.subplots(figsize=(14, 6))
    patient_means = df_all.groupby('patient_name')['mean_wlr'].mean().sort_values(ascending=False)
    colors = plt.cm.Set3(np.linspace(0, 1, len(patient_means)))
    ax.barh(range(len(patient_means)), patient_means.values, color=colors, edgecolor='black')
    ax.set_yticks(range(len(patient_means)))
    ax.set_yticklabels(patient_means.index, fontsize=9)
    ax.set_xlabel('Mean WLR', fontsize=12)
    ax.set_title('Mean WLR per Patient', fontsize=14, fontweight='bold')
    ax.axvline(df_all['mean_wlr'].mean(), color='red', linestyle='--', linewidth=2, label='Global mean')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(output_path / 'WLR_PerPatient.png', dpi=150, bbox_inches='tight')
    print(f"[OK] Saved: WLR_PerPatient.png")
    plt.close()
    
    # 4. Box plot by patient with ALL WLR values (all positions, all measurements)
    # Show only top 50 patients by image count to keep the plot readable
    fig, ax = plt.subplots(figsize=(14, 6))
    patient_order = df_all['patient_name'].value_counts().index[:50]
    patient_data = []
    for p in patient_order:
        # Get all WLR values for this patient (all positions, all focus levels, all measurements)
        patient_wlr_values = np.concatenate(df_all[df_all['patient_name'] == p]['wlr_values'].values)
        patient_data.append(patient_wlr_values)

    bp = ax.boxplot(patient_data, labels=list(patient_order), patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
    ax.set_ylabel('WLR (Wall-to-Lumen Ratio)', fontsize=12)
    ax.set_title('WLR Distribution by Patient (All Measurements) - Top 50 by Image Count', fontsize=14, fontweight='bold')
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_path / 'WLR_BoxPlot_Patients.png', dpi=150, bbox_inches='tight')
    print(f"[OK] Saved: WLR_BoxPlot_Patients.png")
    plt.close()
    
    # 5. Measurement quality vs WLR
    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(df_all['n_measurements'], df_all['mean_wlr'], 
                        c=df_all['success_rate'], cmap='viridis', s=100, alpha=0.6, edgecolor='black')
    ax.set_xlabel('Number of Measurements per Image', fontsize=12)
    ax.set_ylabel('Mean WLR', fontsize=12)
    ax.set_title('WLR vs Measurement Count', fontsize=14, fontweight='bold')
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Success Rate (%)', fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path / 'WLR_vs_MeasurementQuality.png', dpi=150, bbox_inches='tight')
    print(f"[OK] Saved: WLR_vs_MeasurementQuality.png")
    plt.close()


def create_stack_plots(df_stack, df_reliability, output_dir):
    """Create visualizations for Stack analysis."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    sns.set_style("whitegrid")
    
    if df_reliability is not None and len(df_reliability) > 0:
        # 1. Variability across focus levels per location
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(range(len(df_reliability)), df_reliability['std_wlr'].values, 
               color='steelblue', alpha=0.7, edgecolor='black')
        ax.axhline(df_reliability['std_wlr'].mean(), color='red', linestyle='--', 
                  linewidth=2, label=f'Mean std: {df_reliability["std_wlr"].mean():.4f}')
        ax.set_xlabel('Location', fontsize=12)
        ax.set_ylabel('Standard Deviation of WLR', fontsize=12)
        ax.set_title('Measurement Variability Across Focus Levels', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(output_path / 'Stack_Variability.png', dpi=150, bbox_inches='tight')
        print(f"[OK] Saved: Stack_Variability.png")
        plt.close()
        
        # 2. Box plot of WLR per location
        fig, ax = plt.subplots(figsize=(16, 7))
        location_data = df_reliability['wlr_values'].values
        
        # Create readable labels: "Patient: X=xx, Y=yy (n focus levels)"
        labels = [f"{row['patient']}\nX={row['x_coord']:.1f}, Y={row['y_coord']:.1f}\n(n={row['n_focus_levels']})" 
                  for _, row in df_reliability.iterrows()]
        
        bp = ax.boxplot(location_data, tick_labels=labels, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightcoral')
        ax.set_ylabel('WLR (Wall-to-Lumen Ratio)', fontsize=12)
        ax.set_xlabel('Location (Patient, Coordinates, Number of Focus Levels)', fontsize=11)
        ax.set_title('WLR Distribution per Location (Multiple Focus Levels)', fontsize=14, fontweight='bold')
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(output_path / 'Stack_BoxPlot_Locations.png', dpi=150, bbox_inches='tight')
        print(f"[OK] Saved: Stack_BoxPlot_Locations.png")
        plt.close()
        
        # 3. WLR vs Z coordinate (focus level) - scatter plot with connected lines per location
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Use color map for different locations
        colors = plt.cm.tab20(np.linspace(0, 1, len(df_reliability)))
        
        for idx, (_, row) in enumerate(df_reliability.iterrows()):
            label = f"{row['patient']}: X={row['x_coord']:.1f}, Y={row['y_coord']:.1f} (n={row['n_focus_levels']})"
            
            # Sort by Z for proper line connection
            z_vals = row['z_values']
            wlr_vals = row['wlr_values']
            sorted_indices = np.argsort(z_vals)
            z_sorted = z_vals[sorted_indices]
            wlr_sorted = wlr_vals[sorted_indices]
            
            # Plot line first (so scatter points are on top)
            ax.plot(z_sorted, wlr_sorted, color=colors[idx], alpha=0.4, linewidth=1.5, zorder=1)
            # Then scatter points
            ax.scatter(z_sorted, wlr_sorted, 
                      alpha=0.7, s=100, color=colors[idx], 
                      label=label, edgecolors='black', linewidth=0.5, zorder=2)
        
        ax.set_xlabel('Z Coordinate (Focus Level)', fontsize=12)
        ax.set_ylabel('WLR (Wall-to-Lumen Ratio)', fontsize=12)
        ax.set_title('WLR vs Focus Level (Z) - All Locations', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, 
                 title='Location (Patient: X, Y)', framealpha=0.9)
        plt.tight_layout()
        plt.savefig(output_path / 'Stack_WLR_vs_Focus.png', dpi=150, bbox_inches='tight')
        print(f"[OK] Saved: Stack_WLR_vs_Focus.png")
        plt.close()
        
        # 4. Individual location plots (top 6 with most focus levels)
        top_locations = df_reliability.nlargest(6, 'n_focus_levels')
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        # Find global y-axis range across all top 6 locations
        all_wlr_values = []
        for _, row in top_locations.iterrows():
            all_wlr_values.extend(row['wlr_values'])
        y_min = min(all_wlr_values) * 0.95  # 5% margin below
        y_max = max(all_wlr_values) * 1.05  # 5% margin above
        
        for idx, (_, row) in enumerate(top_locations.iterrows()):
            ax = axes[idx]
            
            # Sort by Z coordinate for proper line connection
            z_vals = row['z_values']
            wlr_vals = row['wlr_values']
            sorted_indices = np.argsort(z_vals)
            z_sorted = z_vals[sorted_indices]
            wlr_sorted = wlr_vals[sorted_indices]
            
            ax.plot(z_sorted, wlr_sorted, 'o-', linewidth=2, markersize=8, color='steelblue')
            ax.set_xlabel('Z (Focus)', fontsize=10)
            ax.set_ylabel('WLR', fontsize=10)
            ax.set_title(f"{row['patient']}\nX={row['x_coord']:.1f}, Y={row['y_coord']:.1f} (n={row['n_focus_levels']})", fontsize=9)
            ax.set_ylim(y_min, y_max)  # Set common y-axis range
            ax.grid(True, alpha=0.3)
            ax.axhline(np.mean(wlr_vals), color='red', linestyle='--', alpha=0.5, label=f'Mean: {np.mean(wlr_vals):.4f}')
            ax.legend(fontsize=8)
        
        plt.suptitle('WLR vs Focus Level - Top 6 Locations', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path / 'Stack_Individual_Locations.png', dpi=150, bbox_inches='tight')
        print(f"[OK] Saved: Stack_Individual_Locations.png")
        plt.close()
        
        # 5. Focus range vs WLR variability
        fig, ax = plt.subplots(figsize=(10, 6))
        scatter = ax.scatter(df_reliability['z_range'], df_reliability['std_wlr'], 
                            c=df_reliability['n_focus_levels'], cmap='viridis', 
                            s=100, alpha=0.6, edgecolor='black')
        ax.set_xlabel('Focus Range (Z_max - Z_min)', fontsize=12)
        ax.set_ylabel('WLR Variability (Std)', fontsize=12)
        ax.set_title('WLR Variability vs Focus Range', fontsize=14, fontweight='bold')
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Number of Focus Levels', fontsize=11)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / 'Stack_FocusRange_vs_Variability.png', dpi=150, bbox_inches='tight')
        print(f"[OK] Saved: Stack_FocusRange_vs_Variability.png")
        plt.close()


if __name__ == "__main__":
    # Define data directories
    vessels_all_dir = Path(r'C:\Data\Jakubicek\AO_retinal\Data\Vessels_ALL_to_May_posbirano11082025')
    stack_dir = Path(r'C:\Data\Jakubicek\AO_retinal\Data\Stack_12_2025')
    
    output_dir = Path(r'C:\Data\Jakubicek\AO_retinal\Data\stats')
    
    print("WLR Database Analysis")
    print("="*80)
    
    # # Analyze Vessels_ALL
    if vessels_all_dir.exists():
        result_vessels = analyze_vessels_all(vessels_all_dir)
        if result_vessels:
            df_all, all_wlr = result_vessels
            create_vessels_all_plots(df_all, all_wlr, output_dir)
            
            # Save summary to Excel
            summary_file = output_dir / "Vessels_ALL_Summary.xlsx"
            df_all.to_excel(summary_file, index=False)
            print(f"\n[OK] Saved: {summary_file}")
    else:
        print(f"Directory not found: {vessels_all_dir}")
    
    # Analyze Stack
    if stack_dir.exists():
        result_stack = analyze_stack(stack_dir)
        if result_stack:
            df_stack, df_reliability = result_stack
            if df_reliability is not None:
                create_stack_plots(df_stack, df_reliability, output_dir / "Stack_Analysis")
                
                # Save reliability results
                reliability_file = output_dir / "Stack_Reliability.xlsx"
                df_reliability.to_excel(reliability_file, index=False)
                print(f"\n[OK] Saved: {reliability_file}")
    else:
        print(f"Directory not found: {stack_dir}")
    
    print(f"\n[OK] Analysis complete! Results saved to: {output_dir}")
