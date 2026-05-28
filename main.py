import os
import json
import logging
import sys
from github import Github, GithubException
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# Configuration & Logging
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Data Models (Enforcing deterministic LLM output)
# ---------------------------------------------------------
class PrivacyAssessment(BaseModel):
    is_violation: bool = Field(description="True if the code actually leaks PII or sensitive data.")
    risk_level: str = Field(description="Low, Medium, High, or Critical")
    reasoning: str = Field(description="One sentence explaining the assessment.")
    remediation: str = Field(description="Actionable fix for the developer.")

# ---------------------------------------------------------
# Core Logic
# ---------------------------------------------------------
class PrivacyGuardrail:
    def __init__(self):
        try:
            self.github_token = os.environ["GITHUB_TOKEN"]
            self.gemini_key = os.environ["GEMINI_API_KEY"]
            self.repo_name = os.environ["GITHUB_REPOSITORY"]
            self.pr_number = int(os.environ["PR_NUMBER"])
        except KeyError as e:
            logger.error(f"Missing required environment variable: {e}")
            sys.exit(1)

        # Initialize LLM with strict temperature for analytical tasks
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=self.gemini_key
        )
        self.parser = JsonOutputParser(pydantic_object=PrivacyAssessment)

    def analyze_snippet(self, code: str) -> dict:
        """Runs the LangChain evaluation on the flagged code."""
        template = """
        You are a Senior Privacy & Security Engineer. 
        A static analysis tool (Semgrep) flagged the following code for potentially leaking 
        Personally Identifiable Information (PII) or secrets.
        
        Analyze the code. Determine if it is a TRUE POSITIVE (actual risk) or a FALSE POSITIVE (safe).
        
        Code Snippet:
        {code}
        
        {format_instructions}
        """
        prompt = PromptTemplate(
            template=template,
            input_variables=["code"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

        chain = prompt | self.llm | self.parser
        
        try:
            return chain.invoke({"code": code})
        except Exception as e:
            logger.error(f"LLM Evaluation failed: {e}")
            return {"is_violation": True, "risk_level": "Unknown", "reasoning": "AI evaluation failed.", "remediation": "Manual review required."}

    def execute(self):
        """Main orchestrator function."""
        logger.info("Starting AI Privacy Guardrail analysis...")
        
        if not os.path.exists("semgrep-results.json"):
            logger.info("No Semgrep results file found. Exiting gracefully.")
            return

        with open("semgrep-results.json", "r") as f:
            results = json.load(f)

        findings = results.get("results", [])
        if not findings:
            logger.info("Semgrep found no privacy issues. PR is safe to merge.")
            return

        logger.info(f"Semgrep flagged {len(findings)} potential issues. Initiating AI Assessment.")
        
        try:
            gh = Github(self.github_token)
            repo = gh.get_repo(self.repo_name)
            pr = repo.get_pull(self.pr_number)
        except GithubException as e:
            logger.error(f"Failed to connect to GitHub API: {e}")
            sys.exit(1)

        block_merge = False

        for finding in findings:
            code_snippet = finding.get("extra", {}).get("lines", "")
            file_path = finding.get("path", "Unknown file")
            
            logger.info(f"Analyzing {file_path}...")
            assessment = self.analyze_snippet(code_snippet)
            
            if assessment.get("is_violation"):
                block_merge = True
                
                comment = (
                    f"## AI Privacy Guardrail Alert\n\n"
                    f"**File:** `{file_path}`\n"
                    f"**Risk Level:** {assessment.get('risk_level')}\n\n"
                    f"**Flagged Code:**\n```javascript\n{code_snippet}\n```\n\n"
                    f"**Agent Reasoning:**\n> {assessment.get('reasoning')}\n\n"
                    f"**Suggested Remediation:**\n`{assessment.get('remediation')}`\n\n"
                    f"---\n*This assessment was automatically generated by the AI Privacy Guardrail using Semgrep & LangChain.*"
                )
                
                pr.create_issue_comment(comment)
                logger.info(f"Posted violation comment on PR #{self.pr_number}")

        if block_merge:
            logger.error("True Positive privacy violations detected. Failing CI pipeline.")
            sys.exit(1)
        else:
            logger.info("All flagged issues were determined to be False Positives by the AI. Pipeline passing.")

if __name__ == "__main__":
    guardrail = PrivacyGuardrail()
    guardrail.execute()