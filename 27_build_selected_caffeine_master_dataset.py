import time
from pathlib import Path

import pandas as pd
import requests


BASE_URL = "https://pk-db.com/api/v1"
TARGET_DRUG = "caffeine"

SELECTED_STUDIES = [
    "Lenuzza2016",
    "Jost1987",
    "Balogh1992",
    "PVLDrugs",
    "He2017",
    "Edwards2017",
    "McQuilkin1995",
    "Donzelli2014",
]

DATA_DIR = Path("data")
EXCEL_DIR = DATA_DIR / "selected_caffeine_excels"

DATA_DIR.mkdir(exist_ok=True)
EXCEL_DIR.mkdir(exist_ok=True)

MASTER_OUTPUT = DATA_DIR / "selected_caffeine_concentration_master_dataset.csv"
FILES_OUTPUT = DATA_DIR / "selected_caffeine_excel_files.csv"


def find_excel_files_for_selected_studies(max_pages: int = 900) -> pd.DataFrame:
    """
    Search PK-DB _datafiles endpoint and find .xlsx files
    for the selected caffeine studies.
    """
    selected_lower = {study.lower(): study for study in SELECTED_STUDIES}
    matched = []

    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/_datafiles/?page={page}"

        try:
            response = requests.get(url, timeout=20)
        except Exception as e:
            print(f"Request failed on page {page}: {e}")
            continue

        if response.status_code != 200:
            print(f"Failed page {page}: {response.status_code}")
            continue

        json_data = response.json()
        files = json_data["data"]["data"]

        for item in files:
            file_url = str(item.get("file", ""))
            file_lower = file_url.lower()

            if not file_lower.endswith(".xlsx"):
                continue

            for study_lower, study_name in selected_lower.items():
                if study_lower in file_lower:
                    row = {
                        "study_name": study_name,
                        "file": file_url,
                        "id": item.get("id"),
                    }

                    if row not in matched:
                        matched.append(row)

        pd.DataFrame(matched).to_csv(FILES_OUTPUT, index=False)

        print(f"Checked page {page}, matched Excel files: {len(matched)}")

        if not json_data.get("next_page_url"):
            break

        found_studies = set([m["study_name"] for m in matched])
        if set(SELECTED_STUDIES).issubset(found_studies):
            print("Found Excel files for all selected studies.")
            break

    return pd.DataFrame(matched)


def download_excel(study_name: str, url: str) -> Path | None:
    """
    Download Excel file for one study.
    """
    output_path = EXCEL_DIR / f"{study_name}.xlsx"

    if output_path.exists():
        print(f"Already downloaded: {output_path}")
        return output_path

    try:
        response = requests.get(url, timeout=60)
    except Exception as e:
        print(f"Download failed for {study_name}: {e}")
        return None

    if response.status_code != 200:
        print(f"Download failed for {study_name}: status {response.status_code}")
        return None

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"Downloaded: {output_path}")
    return output_path


def extract_caffeine_concentration_rows(
    excel_path: Path,
    study_name: str
) -> pd.DataFrame:
    """
    Read all sheets from one Excel file and extract caffeine concentration rows.

    This is flexible because PK-DB Excel files may use slightly different
    column names across studies.
    """
    extracted = []

    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"Could not open {excel_path}: {e}")
        return pd.DataFrame()

    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet)
        except Exception as e:
            print(f"Could not read {study_name} sheet {sheet}: {e}")
            continue

        if df.empty:
            continue

        # Remove duplicated metadata/header row if present
        if "Study" in df.columns:
            df = df[df["Study"].astype(str).str.lower() != "study"].copy()

        # Normalize column lookup
        col_map = {str(c).lower().strip(): c for c in df.columns}

        measurement_col = (
            col_map.get("measurement")
            or col_map.get("measurement_type")
            or col_map.get("measurement type")
        )

        substance_col = col_map.get("substance")
        time_col = col_map.get("time")
        value_col = col_map.get("value")
        mean_col = col_map.get("mean")
        unit_col = col_map.get("unit")
        time_unit_col = col_map.get("time_unit") or col_map.get("time unit")
        tissue_col = col_map.get("tissue")
        id_col = (
            col_map.get("id")
            or col_map.get("individual")
            or col_map.get("individual_id")
        )
        label_col = col_map.get("label")
        intervention_col = col_map.get("intervention")
        method_col = col_map.get("method")

        # Need at least substance, time, and concentration value
        if substance_col is None or time_col is None:
            continue

        concentration_col = value_col if value_col is not None else mean_col

        if concentration_col is None:
            continue

        temp = df.copy()

        # Keep only concentration rows if measurement column exists
        if measurement_col is not None:
            temp = temp[
                temp[measurement_col].astype(str).str.lower().str.strip()
                == "concentration"
            ].copy()

        # Keep only caffeine rows
        temp = temp[
            temp[substance_col].astype(str).str.lower().str.strip()
            == TARGET_DRUG
        ].copy()

        if temp.empty:
            continue

        # IMPORTANT FIX:
        # Create clean dataframe using temp.index, so scalar columns align properly.
        clean = pd.DataFrame(index=temp.index)

        clean["study_name"] = study_name
        clean["source_file"] = excel_path.name
        clean["source_sheet"] = sheet

        clean["individual_id"] = temp[id_col] if id_col is not None else None
        clean["label"] = temp[label_col] if label_col is not None else None
        clean["intervention"] = temp[intervention_col] if intervention_col is not None else None
        clean["measurement"] = (
            temp[measurement_col] if measurement_col is not None else "concentration"
        )
        clean["substance"] = temp[substance_col]
        clean["tissue"] = temp[tissue_col] if tissue_col is not None else None
        clean["method"] = temp[method_col] if method_col is not None else None

        clean["time"] = pd.to_numeric(temp[time_col], errors="coerce")
        clean["time_unit"] = temp[time_unit_col] if time_unit_col is not None else None
        clean["concentration"] = pd.to_numeric(
            temp[concentration_col],
            errors="coerce"
        )
        clean["concentration_unit"] = temp[unit_col] if unit_col is not None else None

        clean = clean.dropna(subset=["time", "concentration"])

        if not clean.empty:
            extracted.append(clean)

    if extracted:
        return pd.concat(extracted, ignore_index=True)

    return pd.DataFrame()


def main():
    print("Finding Excel files for selected caffeine studies...")

    files_df = find_excel_files_for_selected_studies()

    if files_df.empty:
        print("No Excel files found.")
        return

    print("\nMatched Excel files:")
    print(files_df)

    all_rows = []

    for _, row in files_df.iterrows():
        study_name = row["study_name"]
        file_url = row["file"]

        print("\n==============================")
        print(f"Processing study: {study_name}")
        print(f"Excel URL: {file_url}")

        excel_path = download_excel(study_name, file_url)

        if excel_path is None:
            continue

        caffeine_df = extract_caffeine_concentration_rows(
            excel_path=excel_path,
            study_name=study_name
        )

        print(f"Extracted caffeine rows: {len(caffeine_df)}")

        if not caffeine_df.empty:
            all_rows.append(caffeine_df)

            # Save progress after each study
            master_df = pd.concat(all_rows, ignore_index=True)
            master_df = master_df.drop_duplicates()

            master_df.to_csv(MASTER_OUTPUT, index=False)

            print(f"Current master dataset shape: {master_df.shape}")
            print(f"Progress saved to: {MASTER_OUTPUT}")

        time.sleep(0.5)

    if all_rows:
        master_df = pd.concat(all_rows, ignore_index=True)
        master_df = master_df.drop_duplicates()

        master_df.to_csv(MASTER_OUTPUT, index=False)

        print("\n==============================")
        print("Finished building master dataset.")
        print("Final shape:", master_df.shape)

        print("\nRows by study:")
        print(master_df["study_name"].value_counts(dropna=False))

        print("\nRows by tissue:")
        print(master_df["tissue"].value_counts(dropna=False))

        print("\nConcentration units:")
        print(master_df["concentration_unit"].value_counts(dropna=False))

        print(f"\nSaved final master dataset to: {MASTER_OUTPUT}")
    else:
        print("No caffeine concentration rows extracted.")


if __name__ == "__main__":
    main()
