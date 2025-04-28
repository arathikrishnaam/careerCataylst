import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
import time
import re
import json
import requests
from datetime import datetime, timedelta

from chains import Chain
from portfolio import Portfolio
from utils import clean_text
from resume import create_resume_checker, init_resume_checker
from resources import display_resources  # Import the main function from resources.py

# Function to inject custom CSS
def inject_custom_css():
    try:
        with open("app/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Fallback in case the path is different
        try:
            with open("styles.css") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            st.error("Could not find styles.css file")

# Function to extract retry time from error message
def extract_retry_time(error_message):
    match = re.search(r'try again in (\d+)m([\d\.]+)s', error_message)
    if match:
        minutes = int(match.group(1))
        seconds = float(match.group(2))
        return f"{minutes} minutes and {int(seconds)} seconds"
    return "some time"

# Function to check remaining tokens (you'll need to implement this based on your API)
def get_remaining_tokens():
    # This is a placeholder - implement your actual API check
    # You could store daily usage in session state or call your API provider
    if 'token_usage' not in st.session_state:
        st.session_state.token_usage = 0
        st.session_state.last_reset = datetime.now()
    
    # Reset counter if it's a new day
    if (datetime.now() - st.session_state.last_reset).days >= 1:
        st.session_state.token_usage = 0
        st.session_state.last_reset = datetime.now()
    
    return max(0, 100000 - st.session_state.token_usage)

# Function to update token usage
def update_token_usage(tokens_used):
    if 'token_usage' not in st.session_state:
        st.session_state.token_usage = 0
    
    st.session_state.token_usage += tokens_used

# Animated loading placeholder
def animated_loading():
    with st.empty():
        for i in range(5):
            st.markdown(f"""
            <div class="loading-animation">
                <div class="dot-pulse dot-{i+1}"></div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.1)

# Modified LLM wrapper with fallback
class LLMWrapper:
    def __init__(self, chain):
        self.chain = chain
        self.primary_model = "llama-3.3-70b-versatile"  # Adjust based on your actual model name
        self.fallback_model = None  # Configure your fallback model if available
    
    def extract_jobs(self, data):
        try:
            result = self.chain.extract_jobs(data)
            # Estimate token usage (rough estimate)
            estimated_tokens = len(data) // 4  # Rough estimate: 4 chars ≈ 1 token
            update_token_usage(estimated_tokens)
            return result
        except Exception as e:
            error_message = str(e)
            if "rate_limit_exceeded" in error_message:
                if self.fallback_model:
                    st.info("Switching to backup model due to rate limits...")
                    # Implement fallback model logic here
                    return []  # Return empty for now, replace with actual fallback
                else:
                    retry_time = extract_retry_time(error_message)
                    st.warning(f"⚠️ API rate limit reached. Please try again in {retry_time} or upgrade your plan.")
                    st.markdown("<a href='https://console.groq.com/settings/billing' target='_blank' class='upgrade-link'>Upgrade Plan</a>", unsafe_allow_html=True)
                    return []
            else:
                raise e
    
    def write_mail(self, job, links):
        try:
            result = self.chain.write_mail(job, links)
            # Estimate token usage
            estimated_tokens = (len(json.dumps(job)) + len(json.dumps(links))) // 4
            update_token_usage(estimated_tokens)
            return result
        except Exception as e:
            error_message = str(e)
            if "rate_limit_exceeded" in error_message:
                retry_time = extract_retry_time(error_message)
                return f"""
                **Rate Limit Reached**
                
                Unable to generate email at this time due to API rate limits.
                Please try again in {retry_time} or consider upgrading your plan.
                
                You can still use the job information and portfolio links to craft your own email.
                """
            else:
                raise e

def create_email_generator(llm_wrapper, portfolio, clean_text):
    # Display token usage in sidebar
    remaining = get_remaining_tokens()
    used = 100000 - remaining
    
    st.sidebar.markdown("<div class='token-usage-section'>", unsafe_allow_html=True)
    st.sidebar.markdown("### Token Usage")
    st.sidebar.progress(min(1.0, used / 100000))
    st.sidebar.markdown(f"<div class='token-text'>Used: {used:,} / 100,000 daily tokens</div>", unsafe_allow_html=True)
    
    if used > 90000:
        st.sidebar.warning("⚠️ Approaching daily token limit")
    
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    # Main email generator interface
    with st.container():
        st.markdown('<div class="section fade-in">', unsafe_allow_html=True)
        st.markdown('<h1 class="app-title">✉️ Cold Mail Generator</h1>', unsafe_allow_html=True)
        
        with st.form(key='email_generator_form'):
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            url_input = st.text_input("Enter a job posting URL:", 
                                     value="https://jobs.nike.com/job/R-33460",
                                     placeholder="https://example.com/job-posting")
            submit_button = st.form_submit_button("Generate Email", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if submit_button:
            if remaining < 5000:
                st.warning("⚠️ You're running low on tokens for today. Results may be limited.")
            
            try:
                with st.spinner("Working on your cold email..."):
                    # Visual feedback for loading
                    st.markdown('<div class="progress-indicator">', unsafe_allow_html=True)
                    animated_loading()
                    
                    # Actual processing
                    loader = WebBaseLoader([url_input])
                    data = clean_text(loader.load().pop().page_content)
                    portfolio.load_portfolio()
                    
                    # Check data length and warn if too large
                    if len(data) > 10000:
                        st.warning("⚠️ This job posting is quite long. Processing may use a significant portion of your remaining tokens.")
                    
                    jobs = llm_wrapper.extract_jobs(data)
                    
                    if not jobs:
                        st.warning("No job information could be extracted or the process was halted due to rate limits.")
                    else:
                        # Results section
                        st.markdown('<div class="result-section fade-in">', unsafe_allow_html=True)
                        st.markdown('<h2 class="result-title">Generated Email</h2>', unsafe_allow_html=True)
                        
                        for i, job in enumerate(jobs):
                            skills = job.get('skills', [])
                            links = portfolio.query_links(skills)
                            
                            # Show job details
                            with st.expander(f"Job Details: {job.get('title', 'Position')}", expanded=False):
                                st.json(job)
                            
                            # Generate and show email
                            email = llm_wrapper.write_mail(job, links)
                            
                            # Create a card for each email
                            st.markdown(f'<div class="email-card">', unsafe_allow_html=True)
                            st.markdown(f'<h3>Email for: {job.get("title", "Job Position")}</h3>', unsafe_allow_html=True)
                            st.code(email, language='markdown')
                            
                            # Add copy button functionality
                            if st.button(f"Copy Email {i+1}", key=f"copy_{i}"):
                                st.info("Email copied to clipboard! (Note: You may need to manually copy in some browsers)")
                                st.markdown(f"""
                                <textarea id="copy-text-{i}" style="position: absolute; left: -9999px;">{email}</textarea>
                                <script>
                                    navigator.clipboard.writeText(document.getElementById("copy-text-{i}").value);
                                </script>
                                """, unsafe_allow_html=True)
                            
                            st.markdown(f'</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Update remaining tokens display after processing
                        st.sidebar.markdown("<div class='token-usage-section'>", unsafe_allow_html=True)
                        st.sidebar.markdown("### Updated Token Usage")
                        remaining = get_remaining_tokens()
                        used = 100000 - remaining
                        st.sidebar.progress(min(1.0, used / 100000))
                        st.sidebar.markdown(f"<div class='token-text'>Used: {used:,} / 100,000 daily tokens</div>", unsafe_allow_html=True)
                        st.sidebar.markdown("</div>", unsafe_allow_html=True)
                
            except Exception as e:
                error_message = str(e)
                st.markdown('<div class="error-message bounce">', unsafe_allow_html=True)
                
                if "rate_limit_exceeded" in error_message:
                    retry_time = extract_retry_time(error_message)
                    st.error(f"Rate limit exceeded. Please try again in {retry_time} or upgrade your plan.")
                    st.markdown("<a href='https://console.groq.com/settings/billing' target='_blank' class='upgrade-link'>Upgrade Plan</a>", unsafe_allow_html=True)
                    
                    # Update session state to reflect we've hit the limit
                    st.session_state.token_usage = 100000
                elif "URL" in error_message or "404" in error_message:
                    st.error(f"Could not access the URL. Please check if the job posting link is valid and accessible.")
                else:
                    st.error(f"An Error Occurred: {e}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Provide helpful tips when errors occur
                st.markdown("""
                ### Troubleshooting Tips:
                - Ensure the URL is accessible and not behind a login
                - Try a different job posting URL
                - Wait until tomorrow if you've hit your rate limit
                - Consider breaking down large job postings into smaller chunks
                """)
        
        st.markdown('</div>', unsafe_allow_html=True)

def create_app_header():
    st.markdown("""
    <div class="app-header fade-in">
        <h1>Job Application Assistant</h1>
        <p>Tools to help you land your dream job</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        layout="wide", 
        page_title="Job Application Assistant", 
        page_icon="💼",
        initial_sidebar_state="expanded"
    )
    
    # Inject custom CSS
    inject_custom_css()
    
    # Initialize resume checker
    init_resume_checker()
    
    # Create app header
    create_app_header()
    
    # Create sidebar for navigation with improved styling
    st.sidebar.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
    st.sidebar.title("Navigation")
    st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    app_mode = st.sidebar.radio("Choose the tool:", 
                              ["Cold Email Generator", "Resume ATS Checker", "Resource Recommendation"])  # Added the new option
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Add info section to sidebar
    st.sidebar.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
    st.sidebar.markdown("""
    ### About
    This app helps you:
    - Generate personalized cold emails
    - Check resume compatibility with ATS systems
    - Find learning resources and references
    """)  # Updated the about section
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize components
    chain = Chain()
    llm_wrapper = LLMWrapper(chain)  # Use our wrapper instead of direct chain
    portfolio = Portfolio()
    
    # Display the selected application
    if app_mode == "Cold Email Generator":
        create_email_generator(llm_wrapper, portfolio, clean_text)
    elif app_mode == "Resume ATS Checker":
        create_resume_checker()
    elif app_mode == "Resource Recommendation": 
        display_resources()  # Call the function from resources.py

    # Add footer with version and help info
    st.markdown("""
    <div class="footer fade-in">
        <p>Job Application Assistant | Created with Streamlit</p>
        <p class="version-text">v1.0.2 - Added Resource Recommendation tool</p>
        <p><a href="mailto:support@example.com" class="help-link">Need help?</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()