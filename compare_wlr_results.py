#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compare WLR (wall-to-lumen ratio) measurements between MATLAB and Python implementations.
Loads Excel files from both results directories and performs statistical comparison.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats


def load_excel_files(directory):
    """Load all Excel files from directory into a dictionary."""
    results = {}
    path = Path(directory)
    
    for xlsx_file in sorted(path.glob('*.xlsx')):
        try:
            df = pd.read_excel(xlsx_file)
            # Extract filename without extension
            filename = xlsx_file.stem
            results[filename] = df
        except Exception as e:
            print(f"Error loading {xlsx_file.name}: {e}")
    
    return results


def extract_wlr_values(df):
    """Extract WLR_Left and WLR_Right values, excluding -1 (NaN marker)."""
    wlr_values = []
    
    if 'WLR_Left' in df.columns:
        wlr_left = df['WLR_Left'].values
        wlr_left = wlr_left[wlr_left >= 0]  # Exclude -1 (NaN marker)
        wlr_values.extend(wlr_left)
    
    if 'WLR_Right' in df.columns:
        wlr_right = df['WLR_Right'].values
        wlr_right = wlr_right[wlr_right >= 0]  # Exclude -1 (NaN marker)
        wlr_values.extend(wlr_right)
    
    return np.array(wlr_values)


def compare_results(matlab_dir, python_dir):
    """Compare WLR measurements between MATLAB and Python implementations."""
    print("Loading MATLAB results...")
    matlab_results = load_excel_files(matlab_dir)
    
    print("Loading Python results...")
    python_results = load_excel_files(python_dir)
    
    # Find common files
    common_files = set(matlab_results.keys()) & set(python_results.keys())
    print(f"\nFound {len(common_files)} common files to compare")
    print(f"MATLAB files: {len(matlab_results)}")
    print(f"Python files: {len(python_results)}")
    
    if not common_files:
        print("ERROR: No common files found!")
        return
    
    # Comparison results
    comparison_data = []
    all_wlr_matlab = []
    all_wlr_python = []
    
    print("\n" + "="*80)
    print("Individual File Comparison")
    print("="*80)
    
    for filename in sorted(common_files):
        matlab_df = matlab_results[filename]
        python_df = python_results[filename]
        
        # Extract WLR values
        wlr_matlab = extract_wlr_values(matlab_df)
        wlr_python = extract_wlr_values(python_df)
        
        all_wlr_matlab.extend(wlr_matlab)
        all_wlr_python.extend(wlr_python)
        
        # Calculate statistics for this file
        n_matlab = len(wlr_matlab)
        n_python = len(wlr_python)
        
        if len(wlr_matlab) > 0 and len(wlr_python) > 0:
            mean_matlab = np.mean(wlr_matlab)
            mean_python = np.mean(wlr_python)
            std_matlab = np.std(wlr_matlab)
            std_python = np.std(wlr_python)
            
            # Mean difference and percentage
            diff_mean = mean_python - mean_matlab
            pct_diff = (diff_mean / mean_matlab * 100) if mean_matlab != 0 else 0
            
            comparison_data.append({
                'File': filename,
                'MATLAB_N': n_matlab,
                'Python_N': n_python,
                'MATLAB_Mean': mean_matlab,
                'Python_Mean': mean_python,
                'MATLAB_Std': std_matlab,
                'Python_Std': std_python,
                'Mean_Diff': diff_mean,
                'Mean_Diff_%': pct_diff
            })
            
            print(f"\n{filename}")
            print(f"  MATLAB: N={n_matlab:3d}, Mean={mean_matlab:.4f} ± {std_matlab:.4f}")
            print(f"  Python: N={n_python:3d}, Mean={mean_python:.4f} ± {std_python:.4f}")
            print(f"  Difference: {diff_mean:+.4f} ({pct_diff:+.2f}%)")
    
    # Overall statistics
    print("\n" + "="*80)
    print("Overall Statistics")
    print("="*80)
    
    all_wlr_matlab = np.array(all_wlr_matlab)
    all_wlr_python = np.array(all_wlr_python)
    
    print(f"\nTotal measurements:")
    print(f"  MATLAB: {len(all_wlr_matlab)} measurements from {len(common_files)} files")
    print(f"  Python: {len(all_wlr_python)} measurements from {len(common_files)} files")
    
    if len(all_wlr_matlab) != len(all_wlr_python):
        print(f"\n⚠ Note: Data are not paired (different number of measurements)")
        print(f"  Using independent samples statistical tests")
    
    print(f"\nWLR Statistics (MATLAB):")
    print(f"  Mean:    {np.mean(all_wlr_matlab):.4f}")
    print(f"  Std:     {np.std(all_wlr_matlab):.4f}")
    print(f"  Min:     {np.min(all_wlr_matlab):.4f}")
    print(f"  Max:     {np.max(all_wlr_matlab):.4f}")
    print(f"  Median:  {np.median(all_wlr_matlab):.4f}")
    
    print(f"\nWLR Statistics (Python):")
    print(f"  Mean:    {np.mean(all_wlr_python):.4f}")
    print(f"  Std:     {np.std(all_wlr_python):.4f}")
    print(f"  Min:     {np.min(all_wlr_python):.4f}")
    print(f"  Max:     {np.max(all_wlr_python):.4f}")
    print(f"  Median:  {np.median(all_wlr_python):.4f}")
    
    # Difference in means (independent samples)
    mean_diff = np.mean(all_wlr_python) - np.mean(all_wlr_matlab)
    print(f"\nMean Difference (Python - MATLAB):")
    print(f"  Absolute: {mean_diff:+.4f}")
    print(f"  Relative: {(mean_diff / np.mean(all_wlr_matlab) * 100):+.2f}%")
    
    # Independent samples t-test (for unpaired data)
    t_stat, p_value = stats.ttest_ind(all_wlr_python, all_wlr_matlab)
    print(f"\nIndependent samples t-test:")
    print(f"  t-statistic: {t_stat:.4f}")
    print(f"  p-value:     {p_value:.4e}")
    
    if p_value < 0.05:
        print(f"  Result: Statistically significant difference (p < 0.05)")
    else:
        print(f"  Result: No statistically significant difference (p >= 0.05)")
    
    # Mann-Whitney U test (non-parametric alternative)
    u_stat, p_value_mw = stats.mannwhitneyu(all_wlr_python, all_wlr_matlab, alternative='two-sided')
    print(f"\nMann-Whitney U test (non-parametric):")
    print(f"  U-statistic: {u_stat:.4f}")
    print(f"  p-value:     {p_value_mw:.4e}")
    
    if p_value_mw < 0.05:
        print(f"  Result: Statistically significant difference (p < 0.05)")
    else:
        print(f"  Result: No statistically significant difference (p >= 0.05)")
    
    # Create comparison dataframe
    comparison_df = pd.DataFrame(comparison_data)
    
    # Create output directory for comparison results
    output_dir = Path(matlab_dir).parent / "comp_methods_stats"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save comparison to Excel
    output_file = output_dir / "WLR_Comparison_MATLAB_vs_Python.xlsx"
    comparison_df.to_excel(output_file, index=False)
    print(f"\n✓ Comparison saved to: {output_file}")
    
    # Create visualizations (independent samples - no scatter plot or correlation)
    create_visualizations(all_wlr_matlab, all_wlr_python, comparison_df, output_dir)


def create_visualizations(wlr_matlab, wlr_python, comparison_df, output_dir):
    """Create comparison plots for independent samples."""
    # output_dir is already the comp_methods_stats directory
    
    # Set style
    sns.set_style("whitegrid")
    
    # 1. Box plot comparison (works for independent samples)
    fig, ax = plt.subplots(figsize=(10, 6))
    data_for_box = [wlr_matlab, wlr_python]
    bp = ax.boxplot(data_for_box, labels=['MATLAB', 'Python'], patch_artist=True)
    bp['boxes'][0].set_facecolor('lightblue')
    bp['boxes'][1].set_facecolor('lightcoral')
    ax.set_ylabel('WLR (Wall-to-Lumen Ratio)', fontsize=12)
    ax.set_title('WLR Distribution: MATLAB vs Python', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'WLR_Comparison_BoxPlot.png', dpi=150, bbox_inches='tight')
    print(f"✓ Saved: WLR_Comparison_BoxPlot.png")
    plt.close()
    
    # 2. Violin plot (alternative distribution view)
    fig, ax = plt.subplots(figsize=(10, 6))
    parts = ax.violinplot([wlr_matlab, wlr_python], positions=[1, 2], showmeans=True, showmedians=True)
    ax.set_xticks([1, 2])
    ax.set_xticklabels(['MATLAB', 'Python'])
    ax.set_ylabel('WLR (Wall-to-Lumen Ratio)', fontsize=12)
    ax.set_title('WLR Distribution: MATLAB vs Python (Violin Plot)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_dir / 'WLR_Comparison_Violin.png', dpi=150, bbox_inches='tight')
    print(f"✓ Saved: WLR_Comparison_Violin.png")
    plt.close()
    
    # 3. Histogram overlay (distribution comparison)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(wlr_matlab, bins=30, alpha=0.6, color='blue', label='MATLAB', edgecolor='black')
    ax.hist(wlr_python, bins=30, alpha=0.6, color='red', label='Python', edgecolor='black')
    ax.axvline(np.mean(wlr_matlab), color='blue', linestyle='--', linewidth=2, label=f'MATLAB Mean: {np.mean(wlr_matlab):.4f}')
    ax.axvline(np.mean(wlr_python), color='red', linestyle='--', linewidth=2, label=f'Python Mean: {np.mean(wlr_python):.4f}')
    ax.set_xlabel('WLR (Wall-to-Lumen Ratio)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('WLR Distribution Overlay', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_dir / 'WLR_Comparison_Histogram.png', dpi=150, bbox_inches='tight')
    print(f"✓ Saved: WLR_Comparison_Histogram.png")
    plt.close()
    
    # 4. Per-file comparison bar plot
    if len(comparison_df) > 0:
        fig, ax = plt.subplots(figsize=(14, 6))
        
        x = np.arange(len(comparison_df))
        width = 0.35
        
        ax.bar(x - width/2, comparison_df['MATLAB_Mean'], width, label='MATLAB', alpha=0.8)
        ax.bar(x + width/2, comparison_df['Python_Mean'], width, label='Python', alpha=0.8)
        
        ax.set_xlabel('Image File', fontsize=12)
        ax.set_ylabel('Mean WLR', fontsize=12)
        ax.set_title('Mean WLR per Image: MATLAB vs Python', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([f"{i+1}" for i in range(len(comparison_df))], fontsize=9)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(output_dir / 'WLR_Comparison_PerImage.png', dpi=150, bbox_inches='tight')
        print(f"✓ Saved: WLR_Comparison_PerImage.png")
        plt.close()


if __name__ == "__main__":
    # Define directories
    matlab_dir = Path(r'C:\Data\Jakubicek\AO_retinal\Data\Tested_data_12_2025\results_matlab')
    python_dir = Path(r'C:\Data\Jakubicek\AO_retinal\Data\Tested_data_12_2025\results_python')
    
    # Check directories exist
    if not matlab_dir.exists():
        print(f"ERROR: MATLAB results directory not found: {matlab_dir}")
        exit(1)
    
    if not python_dir.exists():
        print(f"ERROR: Python results directory not found: {python_dir}")
        exit(1)
    
    print(f"MATLAB results:  {matlab_dir}")
    print(f"Python results:  {python_dir}")
    print()
    
    compare_results(matlab_dir, python_dir)
    
    print("\n✓ Comparison complete!")
