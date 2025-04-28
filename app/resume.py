import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
from dotenv import load_dotenv
import os

def init_resume_checker():
    # Load environment variables if not already loaded in main
    if not os.getenv("GOOGLE_API_KEY"):
        load_dotenv()
    
    # Configure the Gemini API with the key
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyC60OI2Roo80kr2x3CLWJya3-15OckH6XM"))

def get_gemini_response(input_prompt):
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(input_prompt)
    return response.text

def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

def create_resume_checker():
    st.title("Smart ATS Resume Checker")
    st.text("Improve Your Resume for Applicant Tracking Systems")
    
    jd = st.text_area("Paste the Job Description")
    uploaded_file = st.file_uploader("Upload Your Resume", type="pdf",
                                     help="Please upload the PDF file")
    
    submit = st.button("Analyze Resume")
    
    if submit:
        if uploaded_file is not None and jd:
            with st.spinner("Analyzing your resume against the job description..."):
                text = input_pdf_text(uploaded_file)
                
                input_prompt = """
                Act like a skilled or very experienced ATS (Application Tracking System)
                with a deep understanding of tech field, software engineering, data science,
                data analyst and big data engineer. Your task is to evaluate the resume based 
                on the given job description.
                
                You must consider the job market is very competitive and you should provide
                best assistance for improving the resume. Assign the percentage matching based
                on the job description and identify the missing keywords with high accuracy.
                
                Provide the response in the following format:
                JD Match: [percentage]
                Missing Keywords: [comma-separated keywords]
                Profile Summary: [summary text]
                
                Resume: {text}
                Job Description: {jd}
                """
                
                raw_response = get_gemini_response(
                    input_prompt.format(text=text, jd=jd))
                
                try:
                    # Clean the raw response
                    raw_response = raw_response.strip()
                    
                    # Extract JD Match
                    if "JD Match:" in raw_response:
                        jd_match = raw_response.split(
                            "JD Match:")[1].split("\n")[0].strip()
                    else:
                        jd_match = "N/A"
                    
                    # Extract Missing Keywords
                    if "Missing Keywords:" in raw_response:
                        missing_keywords = raw_response.split(
                            "Missing Keywords:")[1].split("\n")[0].strip()
                    else:
                        missing_keywords = "N/A"
                    
                    # Extract Profile Summary
                    if "Profile Summary:" in raw_response:
                        profile_summary = raw_response.split(
                            "Profile Summary:")[1].strip()
                    else:
                        profile_summary = "N/A"
                    
                    # Display results in a nice format
                    st.subheader("ATS Analysis Results")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("JD Match", jd_match)
                    
                    st.subheader("Missing Keywords")
                    if missing_keywords != "N/A":
                        keywords = [keyword.strip() for keyword in missing_keywords.split(",")]
                        for keyword in keywords:
                            st.markdown(f"- {keyword}")
                    else:
                        st.write("No missing keywords identified.")
                    
                    st.subheader("Profile Summary")
                    st.info(profile_summary)
                    
                    st.subheader("Recommendations")
                    st.write("Consider updating your resume to include the missing keywords relevant to your experience.")
                    
                except Exception as e:
                    st.error(f"Error processing the AI response: {e}")
                    st.subheader("Raw Response (For Debugging):")
                    st.text_area("", raw_response, height=300)
        else:
            if not uploaded_file:
                st.warning("Please upload your resume PDF file.")
            if not jd:
                st.warning("Please paste the job description.")

if __name__ == "__main__":
    init_resume_checker()
    create_resume_checker()