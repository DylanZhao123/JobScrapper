import os
import pandas as pd
from config import FIELDS

def export_to_excel(job_list, path):
    if not job_list:
        print("No data to export")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(job_list, columns=FIELDS)
    df.to_excel(path, index=False)
    print(f"Exported: {os.path.abspath(path)}")
