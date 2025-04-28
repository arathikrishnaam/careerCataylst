import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Chain:
    def __init__(self):
        # Initialize ChatGroq with the API key from environment variables
        self.llm = ChatGroq(temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.3-70b-versatile")

    def extract_jobs(self, cleaned_text):
        # Define the prompt template for extracting job postings
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            ### INSTRUCTION:
            The scraped text is from the career's page of a website.
            Your job is to extract the job postings and return them in JSON format containing the 
            following keys: `role`, `experience`, `skills` and `description`.
            Only return the valid JSON.
            ### VALID JSON (NO PREAMBLE):    
            """
        )
        
        # Create the chain to invoke the prompt
        chain_extract = prompt_extract | self.llm
        try:
            # Run the extraction
            res = chain_extract.invoke(input={"page_data": cleaned_text})
            
            # Parse the response to JSON format
            json_parser = JsonOutputParser()
            res_json = json_parser.parse(res.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        
        # Ensure the result is a list, otherwise wrap it in a list
        return res_json if isinstance(res_json, list) else [res_json]

    def write_mail(self, job, links):
        # Define the prompt template for writing a cold email
        prompt_email = PromptTemplate.from_template(
            """
            ### JOB DESCRIPTION:
            {job_description}

            ### INSTRUCTION:
             You are Arathi, a business development executive at AtliQ. AtliQ is an AI & Software Consulting company dedicated to providing 
            innovative solutions to clients through software development and cutting-edge AI techniques.
            Based on your experience in software development and GenAI techniques, AtliQ can offer the most advanced, scalable, and 
            optimized solutions tailored to their specific needs.
            Your task is to write a cold email to the client regarding the job mentioned above, emphasizing AtliQ's expertise in GenAI 
            (including techniques like LLMs, multi-modal models, and computer vision) and ML infrastructure (including model deployment, 
            evaluation, optimization, and data processing).
            Additionally, you should incorporate the most relevant elements from the following links to showcase AtliQ's portfolio: {link_list}
            Remember, you are Arathi, BDE at AtliQ.
            Do not provide a preamble.
            ### EMAIL (NO PREAMBLE):
            """
        )
        
        # Create the chain to invoke the email writing prompt
        chain_email = prompt_email | self.llm
        try:
            # Run the email writing process
            res = chain_email.invoke({"job_description": str(job), "link_list": links})
        except Exception as e:
            raise Exception(f"Error occurred while generating email: {e}")
        
        return res.content

if __name__ == "__main__":
    # Print the loaded API key (for testing purposes, should be kept secure)
    print(os.getenv("GROQ_API_KEY"))
