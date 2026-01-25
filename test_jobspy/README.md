# JobSpy Test

This folder contains tests for the JobSpy tool to evaluate its ability to scrape Indeed jobs with complete information.

## Purpose

Test whether JobSpy can produce job data with the same completeness as our custom scraper, matching the format of `example_output.xlsx`.

## Files

- `test_jobspy_indeed.py` - Main test script
- `output/` - Output directory for test results
  - `jobspy_indeed_output.xlsx` - Excel file with scraped jobs

## Usage

1. Install JobSpy (if not already installed):
   ```bash
   pip install jobspy
   ```

2. Run the test:
   ```bash
   python test_jobspy/test_jobspy_indeed.py
   ```

## Test Parameters

- **Site**: Indeed
- **Keywords**: AI Engineer, Machine Learning Engineer, Data Scientist
- **Location**: San Francisco, CA
- **Results per keyword**: 10

## Expected Output Fields

The test maps JobSpy output to match `example_output.xlsx` format:

- Job Title
- Company Name
- Requirements
- Location
- Salary Range
- Estimated Annual Salary
- Job Description
- Team Size/Business Line Size
- Company Size
- Posted Date
- Job Status
- Platform
- Job Link

## Metrics

The test reports:
- Total jobs scraped
- Elapsed time
- Average time per job
- Field-by-field completeness statistics
- Overall completeness percentage

