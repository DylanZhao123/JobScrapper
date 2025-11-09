import os
import pandas as pd
from config import FIELDS

def export_to_excel(job_list, path):
    if not job_list:
        print("没有数据可导出")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(job_list, columns=FIELDS)
    df.to_excel(path, index=False)
    print(f"已导出：{os.path.abspath(path)}")
