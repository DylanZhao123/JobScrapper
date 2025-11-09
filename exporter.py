import os
import pandas as pd
from config import OUTPUT_EXCEL, FIELDS

def export_to_excel(job_list):
    if not job_list or len(job_list) == 0:
        print("没有可导出的数据")
        return
    data = []
    for job in job_list:
        row = []
        for field in FIELDS:
            row.append(job.get(field, ''))
        data.append(row)
    df = pd.DataFrame(data, columns=FIELDS)
    os.makedirs(os.path.dirname(OUTPUT_EXCEL) or ".", exist_ok=True)
    df.to_excel(OUTPUT_EXCEL, index=False)
    print(f"已成功导出到 {OUTPUT_EXCEL}")
