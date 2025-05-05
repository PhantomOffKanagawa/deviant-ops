# For getting environment variables
import os
# For providing response to Actions
import sys
# For running git diff command
import subprocess
# For making the llm review request
from openai import OpenAI
# For parsing the response from the LLM
from pydantic import BaseModel, Field
# For making the GitHub API request
import requests

# Step 1: Get the environment variables and configurations
SKIPPED_USERS = os.environ.get("SKIPPED_USERS", "").split(",")
PR_AUTHOR = os.environ.get("PR_AUTHOR")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BASE_REF = os.environ.get("BASE_SHA")
HEAD_REF = os.environ.get("HEAD_SHA")
OWNER = os.environ.get("OWNER")
REPO_NAME = os.environ.get("REPO_NAME")
PR_NUMBER = os.environ.get("PR_NUMBER")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Validate the environment variables
if not all([OPENAI_API_KEY, OWNER, REPO_NAME, PR_NUMBER, GITHUB_TOKEN]):
    # Provide context in github actions logs
    print("Missing required environment variables.")
    # Return a failure state to GitHub Actions
    sys.exit(1)

# Step 2: Check if skipped user
if PR_AUTHOR in SKIPPED_USERS:
    # Provide context in github actions logs
    print(f"Skipping review for user: {PR_AUTHOR}")
    # Return a success state to GitHub Actions
    sys.exit(0)

# Explicitly check if BASE_REF and HEAD_REF to avoid warning
if not BASE_REF or not HEAD_REF:
    # Provide context in github actions logs
    print("BASE_REF or HEAD_REF is not set. Cannot proceed with the review.")
    # Return a failure state to GitHub Actions
    sys.exit(1)

# Step 3: Get the diff from the PR
try:
    # First, try to fetch the main branch to ensure it exists
    subprocess.run(["git", "fetch", "origin", "main"], check=False)
    
    try:
        # Use git diff command to get the diff of the PR
        diff = subprocess.check_output(
            # Try to get the diff using the environment variables
            # From https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=opened#pull_request
            ["git", "diff", BASE_REF, HEAD_REF], text=True
        )
    except Exception as e:
        # Fallback: try to get all changes in the current branch
        print("Failed to get diff using origin/main...HEAD, trying alternative approach")
        diff = subprocess.check_output(
            ["git", "diff"], text=True
        )
    
except subprocess.CalledProcessError as e:
    # Catch any errors from the git command
    print(f"Error getting diff: {e}")
    sys.exit(1)
    
# Check if the diff is empty
if not diff.strip():
    print("No changes detected in the PR.")
    # Failback to Allowing the PR to be merged
    sys.exit(0)
    
# Check if the diff is too long
if len(diff) > 4000:
    # Maybe a more context neutral way to truncate would be better
    diff = diff[:4000]  # Truncate to 4000 characters

# Step 3: Send to OpenAI
# Default implementation of OpenAI API client
# So technically not required to pass the api key
client = OpenAI(
    api_key=OPENAI_API_KEY,
)

# Create the Structured Output for the LLM
# https://openai.com/index/introducing-structured-outputs-in-the-api/

# Define the model for the structured output
class CodeReview(BaseModel):
    # Define the fields for the structured output
    # passed is a boolean indicating if the code passed the review
    passed: bool = Field(description="Indicates if the code passed the review")
    # review is a string containing the review message
    review: str = Field(description="The review message for the code")
    # Optional improvements or suggestions for the code if the review fails
    improvements: str | None = Field(description="Optional improvements or suggestions for the code if the review fails")

# Create the prompt for the LLM
# The prompt is designed to be cheerful and fun, asking the LLM to review the code diff for cheerfulness and emoji usage
# But start with a PASS or FAIL statement to make it easier for the code to parse the response
# TODO: More controlling of the LLM's response would be better
prompt = f"""
You are a cheerful code reviewer who loves emoji-filled code. Review the following code diff and determine if it meets our emoji standards.

Review criteria:
1. Added code should contain AT LEAST 5 emojis per 100 lines
2. Emojis **MUST** be contextually relevant to the surrounding code (**not random**)
3. Code should maintain a cheerful, fun tone overall

Instructions:
- Focus ONLY on added lines (ignore removed lines)
- Evaluate both quantity and quality of emoji usage
- Ensure joyful and fun tone in the code (comments and/or code naming)
- Pass only if ALL criteria are met: sufficient emoji count AND proper contextual usage AND cheerful tone
- Do not include mention of the review criteria in your response

The Code Diff To Review:

{diff}

Provide your response as:
- A clear PASS/FAIL determination
- A cheerful review message explaining your decision
- If failing, specific suggestions for improvement (which emojis to add and where)
"""

try:
    # Try to get a response from the OpenAI API
    completion = client.beta.chat.completions.parse(
        # Use the gpt-4o model for the review
        model="gpt-4o",
        # Use the system role to set the context for the LLM
        # Use the user role to provide the prompt
        messages=[
            {"role": "system", "content": "You are a cheerful but discerning code reviewer who loves emoji-filled code."},
            {"role": "user", "content": prompt}
        ],
        response_format=CodeReview,
    )
    
# Get the content of the response
    message_object = completion.choices[0].message.parsed

except Exception as e:
    # Catch any errors from the OpenAI API
    print(f"Error communicating with OpenAI: {e}")
    sys.exit(0)

# Check if message_object is None before accessing attributes
if message_object is None:
    print("Error: No response from OpenAI API.")
    sys.exit(0)
else:
    passed = message_object.passed
    message = message_object.review
    improvements = message_object.improvements

# Provide context in github actions logs
print("LLM Response:")
print(f"Passed: {passed}")
print("Message:")
print(message)
if improvements:
    print("Improvements:")
    print(improvements)

# Step 4: Add comment to PR
# Format the request URI for the GitHub API
# github.repository / REPO_NAME is the full name of the repository in the format "owner/repo"
# Use the issues endpoint to add a comment to the PR as PRs are issues in GitHub
# A PR endpoint would require a filename and commit ID which is more complex to get
request_uri = f"https://api.github.com/repos/{REPO_NAME}/issues/{PR_NUMBER}/comments"
# Set the request headers and body
# Actually following https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28
# Also see https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28#create-a-review-comment-for-a-pull-request
request_headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
    "Content-Type": "application/json",
}

# Create formatted comment body with better styling
comment_body = "## 🧐 Emoji Code Review\n\n"

# Add emoji status badge
if passed:
    comment_body += "### ✅ PASSED\n\n"
else:
    comment_body += "### ❌ FAILED\n\n"

# Add review message
comment_body += f"{message}\n\n"

# Add improvements if any
if improvements and not passed:
    comment_body += "### 💡 Suggested Improvements\n\n"
    comment_body += f"{improvements}\n\n"

# Set the request body
request_body = {
    "body": comment_body
}

# Make the request to the GitHub API to add the comment to the PR
# Using requests library to make the API call
response = requests.post(
    request_uri,
    headers=request_headers,
    json=request_body,
)

# Check if the request was not successful
if response.status_code != 201:
    print("Failed to add comment to PR.")
    print(f"Response: {response.status_code} - {response.text}")
    print(response.json())
    sys.exit(1)
    
# Step 5: Return success state or fail
if passed:
    print("PR passed the LLM review!")
    sys.exit(0)
else:
    print("PR failed the LLM review. Please address the issues.")
    sys.exit(1)