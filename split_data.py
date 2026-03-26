import pandas as pd
import json
import random
from sklearn.model_selection import KFold
import os
from batchgenerators.utilities.file_and_folder_operations import load_json

def create_nnunet_splits_with_fold_info(excel_path, output_json_path, output_excel_path, num_folds=5):
    """
    Načte Excel soubor s daty, rozdělí pacienty pro křížovou validaci,
    uloží split do JSON souboru ve formátu nnU-Net a aktualizuje Excel soubor
    s informacemi o přiřazení k foldům.

    Args:
        excel_path (str): Cesta k XLSX souboru s daty.
        output_json_path (str): Cesta pro uložení výsledného JSON souboru.
        output_excel_path (str): Cesta pro uložení aktualizovaného XLSX souboru.
        num_folds (int): Počet foldů pro křížovou validaci.
    """

    # 1. Načtení dat z XLSX souboru
    try:
        df = pd.read_excel(excel_path)
    except FileNotFoundError:
        print(f"Chyba: Soubor '{excel_path}' nebyl nalezen.")
        return
    except Exception as e:
        print(f"Chyba při načítání souboru Excel: {e}")
        return

    # 2. Získání unikátních jmen pacientů
    unique_patients = df['Patient_name'].unique().tolist()
    random.shuffle(unique_patients) # Náhodné zamíchání pro lepší rozdělení

    print(f"Nalezeno {len(unique_patients)} unikátních pacientů.")

    # 3. Příprava na K-Fold křížovou validaci
    kf = KFold(n_splits=num_folds, shuffle=True, random_state=42)
    
    splits = []

    # Inicializujeme nové sloupce v DataFrame pro každý fold
    # Naplníme je prázdnými stringy nebo None, aby nebyly chyby
    for i in range(num_folds):
        df[f'Fold_{i}'] = ''

    for fold_idx, (train_patient_indices, val_patient_indices) in enumerate(kf.split(unique_patients)):
        train_patients = [unique_patients[i] for i in train_patient_indices]
        val_patients = [unique_patients[i] for i in val_patient_indices]

        # 4. Získání 'ID_name' pro trénovací a validační sady
        train_ids = df[df['Patient_name'].isin(train_patients)]['ID_name'].tolist()
        val_ids = df[df['Patient_name'].isin(val_patients)]['ID_name'].tolist()

        # Ujistíme se, že ve validačních datech nejsou žádní pacienti z trénovacích dat
        train_patient_set = set(train_patients)
        val_patient_set = set(val_patients)
        if not train_patient_set.isdisjoint(val_patient_set):
            print(f"Upozornění: Překrývání pacientů mezi trénovací a validační sadou ve foldu {fold_idx}. Zkontrolujte logiku rozdělení.")

        splits.append({
            'train': train_ids,
            'val': val_ids
        })
        
        print(f"Fold {fold_idx}:")
        print(f"  Trénovací pacienti ({len(train_patients)}): {train_patients[:5]}...")
        print(f"  Validační pacienti ({len(val_patients)}): {val_patients[:5]}...")
        print(f"  Počet trénovacích obrázků: {len(train_ids)}")
        print(f"  Počet validačních obrázků: {len(val_ids)}")
        print("-" * 30)

        # 5. Aktualizace DataFrame o informace o foldu
        # Nastavíme 'Tr' pro řádky patřící do trénovací sady aktuálního foldu
        df.loc[df['Patient_name'].isin(train_patients), f'Fold_{fold_idx}'] = 'Tr'
        # Nastavíme 'Val' pro řádky patřící do validační sady aktuálního foldu
        df.loc[df['Patient_name'].isin(val_patients), f'Fold_{fold_idx}'] = 'Val'

    # 6. Uložení splits do JSON souboru
    try:
        with open(output_json_path, 'w') as f:
            json.dump(splits, f, indent=4)
        print(f"Splits úspěšně uloženy do '{output_json_path}'")
    except Exception as e:
        print(f"Chyba při ukládání JSON souboru: {e}")

    # 7. Uložení aktualizované tabulky do nového XLSX souboru
    try:
        df.to_excel(output_excel_path, index=False)
        print(f"Aktualizovaná tabulka úspěšně uložena do '{output_excel_path}'")
    except Exception as e:
        print(f"Chyba při ukládání aktualizované tabulky: {e}")

if __name__ == "__main__":
    # Nastavte cesty k vašim souborům
    excel_input_file = r'C:\Data\Jakubicek\AO_retinal\Data\Dataset007_AO25\data_list_V3_2.xlsx' # Vstupní soubor Excel/CSV
    json_output_file = r'C:\Data\Jakubicek\AO_retinal\Data\Dataset007_AO25\splits_final.json'
    excel_output_file = r'C:\Data\Jakubicek\AO_retinal\Data\Dataset007_AO25\data_list_V3_2_with_folds.xlsx' # Nový výstupní soubor Excel
    
    # Zkontrolujeme, zda vstupní soubor existuje
    if not os.path.exists(excel_input_file):
        print(f"Chyba: Soubor '{excel_input_file}' nebyl nalezen ve stejném adresáři jako tento skript.")
        print("Ujistěte se, že je soubor XLS/CSV správně pojmenován a umístěn.")
    else:
        create_nnunet_splits_with_fold_info(excel_input_file, json_output_file, excel_output_file, num_folds=5)
    
    # splits = load_json(r'/media/jakubicek/DATA/Jakubicek/AO_retinal/Data/splits_final.json')
