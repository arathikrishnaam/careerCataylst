# CareerCatalyst

CareerCatalyst is a comprehensive job application toolkit designed to help users with their job search. It includes three main tools:

1. **Cold Email Generator** - Creates personalized cold emails for job applications based on job postings.
2. **Resume ATS Checker** - Analyzes resumes against job descriptions to improve ATS compatibility.
3. **Resource Recommendation** - Finds and recommends relevant learning resources from various platforms.


## Features

- **Cold Email Generator**
  - Scrapes job information from URLs
  - Generates personalized emails based on job requirements
  - Includes portfolio matching for relevant skills

- **Resume ATS Checker**
  - Analyzes resume PDF against job descriptions
  - Provides match percentage and missing keywords
  - Offers profile summary and improvement suggestions

- **Resource Recommendation**
  - Searches across YouTube, Google, and GitHub
  - Provides curated learning resources
  - Filters by content type (videos, articles, repositories)

## Getting Started

### Prerequisites

- Python 3.8+
- Required packages (install using `pip install -r requirements.txt`):
  - streamlit
  - langchain
  - langchain-groq
  - chromadb
  - pypdf2
  - google-api-python-client
  - python-dotenv
  - requests
  - pandas
  - scikit-learn

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/arathikrishnaam/careerCataylst.git
   cd careerCataylst
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up API keys:
   Create a `.env` file in the project root with the following keys:
   ```
   GROQ_API_KEY=your_groq_api_key
   GOOGLE_API_KEY=your_google_api_key
   ```

### Running the Application

```
streamlit run main.py
```

## Technical Implementation

### Cold Email Generator
The Cold Email Generator uses LangChain with Groq's Llama 3.3 model to:
1. Extract job details from posting URLs
2. Match skills with portfolio examples
3. Generate personalized cold emails tailored to the job requirements

### Resume ATS Checker
The Resume ATS Checker uses Google's Gemini AI to:
1. Extract text content from uploaded PDF resumes
2. Compare resume content against job descriptions
3. Provide match percentage and identify missing keywords
4. Generate suggestions for resume improvement

### Resource Recommendation
The Resource Recommendation tool uses multiple APIs to:
1. Search for educational content across multiple platforms
2. Rank results using TF-IDF similarity
3. Present organized, filtered results in an intuitive interface

## API Usage

This project uses several APIs:
- Groq API for LLM capabilities (Llama 3.3)
- Google Gemini AI for resume analysis
- Google Custom Search API for resource recommendations
- YouTube Data API v3 for video resources
- GitHub API for repository recommendations

## Future Enhancements

- Integration with job boards for direct job searching
- Email tracking and follow-up suggestions
- Interview preparation tools
- Salary negotiation assistant
- Portfolio website builder


## Contributors

- [Arathi Krishna](https://github.com/arathikrishnaam) 
- [Sreelakshmi S](https://github.com/ssreelakshmi04) 
- [Shahana KV](https://github.com/ShahanaKV)


## Acknowledgments

- LangChain for providing the framework to build LLM applications
- Groq for their powerful LLM APIs
- Streamlit for the interactive web application framework
