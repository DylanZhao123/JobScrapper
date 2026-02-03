# JobSpy Test Results - Indeed Job Scraping

## Test Summary

**Date**: 2025-11-26  
**Tool**: JobSpy (python-jobspy 1.1.82)  
**Target Site**: Indeed  
**Test Location**: San Francisco, CA  
**Keywords**: AI Engineer, Machine Learning Engineer, Data Scientist  
**Results per keyword**: 10  
**Total jobs scraped**: 30

## Performance Metrics

- **Total elapsed time**: 2.53 seconds
- **Average time per job**: 0.08 seconds
- **Jobs per second**: ~11.9 jobs/second
- **Speed**: Very fast compared to custom scraper

## Data Completeness

### Overall Completeness: 84.1%

### Field-by-Field Statistics

| Field | Completeness | Notes |
|-------|-------------|-------|
| Job Title | 100.0% (30/30) | ✓ Excellent |
| Company Name | 76.7% (23/30) | Some jobs have missing company names |
| Requirements | 90.0% (27/30) | Extracted from description |
| Location | 100.0% (30/30) | ✓ Excellent |
| Salary Range | 83.3% (25/30) | Good coverage |
| Estimated Annual Salary | 83.3% (25/30) | Calculated from salary range |
| Job Description | 100.0% (30/30) | ✓ Excellent |
| Team Size/Business Line Size | 0.0% (0/30) | Not available in JobSpy |
| Company Size | 60.0% (18/30) | Available as company_num_employees |
| Posted Date | 100.0% (30/30) | ✓ Excellent |
| Job Status | 100.0% (30/30) | ✓ Excellent |
| Platform | 100.0% (30/30) | ✓ Excellent |
| Job Link | 100.0% (30/30) | ✓ Excellent |

## Comparison with Custom Scraper

### Advantages of JobSpy:
1. **Speed**: Much faster (0.08s/job vs ~1s/job)
2. **Ease of use**: Simple API, returns DataFrame
3. **Built-in support**: Handles multiple job sites
4. **Salary data**: Good coverage (83.3%)

### Disadvantages of JobSpy:
1. **Company name**: Some missing (76.7% vs our 100%)
2. **Company size**: Lower coverage (60% vs our 60-70%)
3. **Requirements**: Extracted from description, not always accurate
4. **Team Size**: Not available
5. **Dependency issues**: Requires specific numpy version (1.26.3) which needs C compiler on Windows

## Installation Issues

JobSpy has dependency conflicts:
- Requires `numpy==1.26.3` (needs C compiler on Windows)
- Requires `markdownify<0.14.0` (we installed 1.2.2)
- Requires `regex<2025.0.0` (we installed 2025.11.3)

Despite these conflicts, JobSpy still works, but may have compatibility issues in the future.

## Recommendations

1. **For speed**: JobSpy is excellent for quick scraping
2. **For completeness**: Custom scraper provides better data quality
3. **For production**: Consider using JobSpy for initial scraping, then enrich with custom scraper for missing fields
4. **For Windows**: Consider using a Python environment with pre-built numpy wheels or install Visual Studio Build Tools

## Sample Output

The test generated `test_jobspy/output/jobspy_indeed_output.xlsx` with 30 jobs in the expected format matching `example_output.xlsx`.

## Conclusion

JobSpy is a fast and convenient tool for Indeed job scraping, achieving 84.1% overall completeness. However, it has some limitations:
- Missing company names in some cases
- No team size information
- Dependency installation issues on Windows

For production use, a hybrid approach might work best: use JobSpy for initial fast scraping, then use custom scraper to fill in missing details.

