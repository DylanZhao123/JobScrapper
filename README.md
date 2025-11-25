# JobScrapper

A web scraping tool for collecting AI-related job postings from US job platforms (LinkedIn, Indeed).  
Generates static Excel reports in the first phase, with potential for expansion into an automated quarterly scraping system.

> ⚠️ **Important**: This tool is for educational and research purposes. Users are responsible for complying with all applicable laws, Terms of Service, and regulations. See [Usage Notes & Compliance](#important-usage-notes--compliance) section for details.

## Features

- **Dual Job Category Scraping**: Scrapes both core AI jobs (high relevance) and AI-related jobs (low relevance) in one run
- **Checkpoint Support**: Resume from breakpoints if scraping is interrupted
- **Automatic Deduplication**: Removes duplicate jobs based on job title and company name
- **Salary Estimation**: Automatically converts hourly/monthly salaries to annual estimates
- **Company Size Extraction**: Multi-level search strategy with caching
- **Location Coverage**: Supports 395 US locations across all 50 states + DC
- **Merged Keyword Search**: Reduces API calls by combining keywords with OR logic

## Installation

### Prerequisites

- Python 3.7+
- ZenRows API key (for bypassing anti-scraping measures)

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### 1. ZenRows API Setup

1. Sign up for a ZenRows account at [https://www.zenrows.com/](https://www.zenrows.com/)
2. Get your API key from the dashboard
3. Create a `.env` file in the project root (you can copy `.env.example` as a template):

```bash
cp .env.example .env
```

Then edit `.env` and add your API key:

```env
ZENROWS_API_KEY=your_zenrows_api_key_here
```

**Note**: The `.env` file is already in `.gitignore` and will not be committed to the repository. Never commit API keys or credentials to version control.

### 2. Configure Scraping Parameters

Edit `config.py` to customize scraping settings:

```python
# Output directory name
RUN_ID = "Merged_Report_001"

# Target site (currently only LinkedIn is supported)
TARGET_SITE = "linkedin"

# Core AI job keywords (high relevance)
# You can customize these keywords to target specific job types
KEYWORDS = ["AI Engineer", "Machine Learning", "Deep Learning", "NLP", "Data Scientist"]

# Use merged keyword search (recommended: reduces API calls)
USE_MERGED_KEYWORDS = True

# Scraping parameters
MAX_PAGES = 10  # Maximum pages per location
LIST_LIMIT = 20000  # Maximum unique jobs in stage 1
DETAIL_LIMIT = 20000  # Maximum jobs to enrich in stage 2
REQUEST_DELAY = 0.3  # Delay between requests (seconds)
```

### 3. Customize Search Keywords

**You can customize the search keywords to target different job categories:**

#### Core Job Keywords (High Relevance)
Location: `config.py` → `KEYWORDS` variable (line ~16)

Modify the `KEYWORDS` list to change what jobs are considered "core" (relevance level = 1):
```python
KEYWORDS = ["Your Keyword 1", "Your Keyword 2", "Your Keyword 3"]
```

#### AI-Related Job Keywords (Low Relevance)
Location: `main_merged.py` → `AI_RELATED_KEYWORDS` variable (line ~88)

The `AI_RELATED_KEYWORDS` list contains 100+ keywords for AI-related jobs (relevance level = 2). You can:
- **Add new keywords**: Add any job-related keywords to expand the search scope
- **Remove keywords**: Remove keywords you're not interested in
- **Modify categories**: Edit the keyword categories (AI Sales, AI Product, etc.)

Example - Adding custom keywords:
```python
AI_RELATED_KEYWORDS = [
    # Your custom category
    "Your Custom Keyword 1", "Your Custom Keyword 2",
    
    # Existing categories...
    "AI Sales", "AI Sales Representative", ...
]
```

**Customization Tips**:
- Keywords are case-insensitive
- Use specific job titles for better results (e.g., "Senior AI Engineer" instead of just "Engineer")
- When `USE_MERGED_KEYWORDS = True`, all keywords in a list are combined with OR logic (e.g., "keyword1" OR "keyword2" OR ...), which reduces API calls significantly
- You can create entirely different keyword sets for different industries or job types
- To scrape only core jobs, you can modify `main_merged.py` to skip the AI-related scraping stage

## Usage

### Run Merged Scraper (Recommended)

The merged scraper (`main_merged.py`) scrapes both core and AI-related jobs in one run:

```bash
python main_merged.py
```

This will:
1. **Stage A**: Scrape core AI jobs (using `config.KEYWORDS`)
2. **Stage B**: Scrape AI-related jobs (100+ keywords including AI Sales, AI Product Manager, etc.)
3. **Stage C**: Merge, deduplicate, and generate final report

Output will be saved to `outputs/{RUN_ID}/merged_report.xlsx`

### Important Usage Notes & Compliance

⚠️ **Legal and Ethical Considerations**

Before using this software, please be aware of the following:

1. **Terms of Service Compliance**
   - **LinkedIn**: This tool accesses LinkedIn through proxy services. Users must comply with LinkedIn's Terms of Service and User Agreement. Automated scraping may violate LinkedIn's terms.
   - **Indeed**: Similar considerations apply to Indeed's Terms of Service.
   - **ZenRows**: Users must comply with ZenRows' Terms of Service and usage policies.

2. **User Responsibility**
   - Users are **solely responsible** for ensuring their use of this software complies with:
     - All applicable laws and regulations in their jurisdiction
     - Terms of Service of target platforms (LinkedIn, Indeed)
     - Terms of Service of third-party services (ZenRows)
     - Data protection and privacy laws (GDPR, CCPA, etc.)

3. **Rate Limiting & Ethical Use**
   - The software includes rate limiting (`REQUEST_DELAY`) to reduce server load
   - Users should respect rate limits and not abuse the services
   - Excessive requests may result in IP bans or account suspension

4. **Data Usage**
   - Collected data should be used responsibly and in compliance with applicable laws
   - Users must respect privacy rights and data protection regulations
   - Do not use collected data for spam, harassment, or other unethical purposes

5. **No Warranty**
   - This software is provided "as is" without warranty
   - The authors make no representations about the legality of web scraping
   - Users assume all legal and financial responsibility for their use

**By using this software, you acknowledge that you have read, understood, and agree to comply with all applicable terms, laws, and regulations.**

### Output Format

The final Excel report includes:

- **relevance level**: 1 = Core AI jobs (high relevance), 2 = AI-related jobs (low relevance)
- **Job Label**: Normalized job title (e.g., "AI Engineer", "Data Scientist")
- **Job Level**: Job level extracted from title (Intern, Junior, Regular, Senior, Management)
- **Job Title**: Original job title
- **Company Name**: Company name
- **Requirements**: Professional requirements extracted from job description
- **Location**: Job location
- **Salary Range**: Original salary range from posting
- **Estimated Annual Salary**: Converted annual salary estimate
- **Job Description**: Full job description
- **Team Size/Business Line Size**: Team or business line size
- **Company Size**: Number of employees
- **Posted Date**: Job posting date
- **Job Status**: Job status (usually "Active")
- **Platform**: Source platform (LinkedIn)
- **Job Link**: URL to the job posting

## Salary Estimation Method

The scraper automatically estimates annual salaries from various formats:

1. **Annual Salary**: If the posting specifies annual/yearly salary, it's used directly
2. **Monthly Salary**: Multiplied by 12 to get annual estimate
3. **Hourly Salary**: Multiplied by 40 hours/week × 52 weeks = 2,080 hours/year
4. **Range Conversion**: If a range is provided (e.g., "$100k - $150k"), the average is calculated
5. **Unit Detection**: If no unit is specified, the scraper infers from the amount:
   - < $200: Treated as hourly
   - < $50,000: Treated as monthly
   - ≥ $50,000: Treated as annual

The estimated annual salary is rounded to the nearest $10.

## Scraping Keywords

### Core AI Jobs (High Relevance)
Location: `config.py` → `KEYWORDS` variable

Default keywords:
- AI Engineer
- Machine Learning
- Deep Learning
- NLP
- Data Scientist

**Customization**: Edit the `KEYWORDS` list in `config.py` to target your specific job categories.

### AI-Related Jobs (Low Relevance)
Location: `main_merged.py` → `AI_RELATED_KEYWORDS` variable (starting at line ~88)

The scraper includes 100+ keywords covering:
- **AI Sales**: AI Sales, AI Business Development, AI Account Manager
- **AI Conversation**: AI Conversational Designer, AI Chatbot Designer, Conversational AI
- **AI Training**: AI Trainer, AI Model Training, Machine Learning Trainer
- **AI Product**: AI Product Manager, AI Product Owner
- **AI + Industry**: AI Healthcare, AI Finance, AI Education, AI Retail, etc.
- **AI Art & Design**: AI Artist, AI Designer, AI UX Designer
- **AI Architecture**: AI Architect, AI Solution Architect
- **AI Governance & Ethics**: AI Governance, AI Ethics, Responsible AI
- **AI Hardware**: AI Hardware Engineer, AI Chip Design
- **AI Operations**: AI DevOps, AI MLOps, AI Platform Engineer
- **Data Annotation**: Data Labeling, Data Annotator
- **Robotics**: Robotics Engineer, Autonomous Systems, RPA

**Customization**: 
- Edit `AI_RELATED_KEYWORDS` in `main_merged.py` to add/remove keywords
- You can create entirely new keyword lists for different job categories
- Keywords are case-insensitive and support partial matching

## Checkpoint System

The scraper supports checkpoint/resume functionality:

- If scraping is interrupted, you can rerun the script and it will resume from the last checkpoint
- Checkpoints are saved automatically during scraping
- If `RUN_ID` changes, old checkpoints are automatically cleared

## Output Structure

```
outputs/
└── {RUN_ID}/
    ├── merged_report.xlsx          # Final merged report
    ├── core_jobs/                  # Core job scraping data
    │   ├── checkpoint.json
    │   ├── stage1_raw_data.json
    │   ├── stage1_unique_data.json
    │   └── stage2_detail_data.json
    ├── ai_related_jobs/            # AI-related job scraping data
    │   ├── checkpoint.json
    │   ├── stage1_raw_data.json
    │   ├── stage1_unique_data.json
    │   └── stage2_detail_data.json
    └── company_cache.json          # Company size cache
```

## Limitations

1. **LinkedIn Rate Limits**: LinkedIn has strict rate limits for unauthenticated/proxy access. Each keyword may only return 10-50 results per location.
2. **API Quota**: ZenRows API has request limits. Set appropriate `REQUEST_DELAY` to avoid exceeding quotas.
3. **Data Completeness**: Some fields (salary, company size) may not be available for all jobs, depending on posting completeness.

## Troubleshooting

### API Key Issues
- Ensure `.env` file exists and contains `ZENROWS_API_KEY`
- Verify your API key is valid and has remaining quota

### Checkpoint Issues
- If you want to start fresh, change `RUN_ID` in `config.py`
- Old checkpoints will be automatically cleared

### Network Issues
- If you see consecutive request failures, check your network connection
- The scraper will automatically retry failed requests

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Important Legal Notices

The MIT License applies to the software code. However, users must also comply with:

- **Third-Party Service Terms**: Terms of Service of ZenRows, LinkedIn, and Indeed
- **Applicable Laws**: All local, state, and federal laws regarding web scraping and data collection
- **Data Protection Regulations**: GDPR, CCPA, and other privacy laws as applicable

**Users are solely responsible for ensuring legal compliance.** The authors and contributors are not liable for any misuse or legal issues arising from the use of this software.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 Python style guidelines
- Add comments for complex logic
- Update documentation (README.md) for new features
- Ensure all output messages are in English
