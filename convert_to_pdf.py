# -*- coding: utf-8 -*-
import subprocess
import sys
import os

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def convert_notebook_to_pdf():
    notebook_file = "US_Job_Market_Analysis.ipynb"
    output_dir = "finding"
    
    methods = [
        ["jupyter", "nbconvert", "--to", "pdf", notebook_file, "--output-dir", output_dir],
        ["python", "-m", "nbconvert", "--to", "pdf", notebook_file, "--output-dir", output_dir],
    ]
    
    for method in methods:
        try:
            print(f"Trying: {' '.join(method)}")
            result = subprocess.run(method, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='ignore')
            if result.returncode == 0:
                print("PDF generated successfully!")
                return True
        except:
            continue
    
    print("Trying to install nbconvert...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "nbconvert", "pypandoc"], check=False)
        result = subprocess.run([sys.executable, "-m", "nbconvert", "--to", "pdf", notebook_file, "--output-dir", output_dir], 
                              capture_output=True, text=True, timeout=120, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            print("PDF generated successfully!")
            return True
    except:
        pass
    
    print("Cannot generate PDF automatically. Please install: pip install nbconvert")
    return False

if __name__ == "__main__":
    convert_notebook_to_pdf()

