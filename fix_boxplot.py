#!/usr/bin/env python3
# Fix box plot to show all WLR measurements per patient

with open("analyze_wlr_database.py", "r") as f:
    content = f.read()

old_section = """    # 4. Box plot by patient
    fig, ax = plt.subplots(figsize=(14, 6))
    patient_data = [df_all[df_all['patient_name'] == p]['mean_wlr'].values for p in df_all['patient_name'].unique()]
    bp = ax.boxplot(patient_data, labels=df_all['patient_name'].unique(), patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
    ax.set_ylabel('WLR (Wall-to-Lumen Ratio)', fontsize=12)
    ax.set_title('WLR Distribution by Patient', fontsize=14, fontweight='bold')
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_path / 'WLR_BoxPlot_Patients.png', dpi=150, bbox_inches='tight')
    print(f"[OK] Saved: WLR_BoxPlot_Patients.png")
    plt.close()"""

new_section = """    # 4. Box plot by patient with ALL WLR values (all positions, all measurements)
    fig, ax = plt.subplots(figsize=(14, 6))
    unique_patients = df_all['patient_name'].unique()
    patient_data = []
    for p in unique_patients:
        # Get all WLR values for this patient (all positions, all focus levels, all measurements)
        patient_wlr_values = np.concatenate(df_all[df_all['patient_name'] == p]['wlr_values'].values)
        patient_data.append(patient_wlr_values)
    
    bp = ax.boxplot(patient_data, labels=unique_patients, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
    ax.set_ylabel('WLR (Wall-to-Lumen Ratio)', fontsize=12)
    ax.set_title('WLR Distribution by Patient (All Measurements)', fontsize=14, fontweight='bold')
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_path / 'WLR_BoxPlot_Patients.png', dpi=150, bbox_inches='tight')
    print(f"[OK] Saved: WLR_BoxPlot_Patients.png")
    plt.close()"""

if old_section in content:
    content = content.replace(old_section, new_section)
    with open("analyze_wlr_database.py", "w") as f:
        f.write(content)
    print("[OK] Box plot updated - now shows ALL WLR measurements per patient")
else:
    print("[ERROR] Could not find old section to replace")
