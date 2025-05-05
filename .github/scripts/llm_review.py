# For getting environment variables
import os
# For providing response to Actions
import sys
# For running git diff command
import subprocess
# For making the llm review request
from openai import OpenAI
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
    # Maybe a more context nuetral way to truncate would be better
    diff = diff[:4000]  # Truncate to 4000 characters

# Step 3: Send to OpenAI
# Default implementation of OpenAI API client
# So technically not required to pass the api key
client = OpenAI(
    api_key=OPENAI_API_KEY,
)

# Create the prompt for the LLM
# The prompt is designed to be cheerful and fun, asking the LLM to review the code diff for cheerfulness and emoji usage
# But start with a PASS or FAIL statement to make it easier for the code to parse the response
# TODO: More controlling of the LLM's response would be better
prompt = f"""
You are a cheerful code reviewer who loves emoji-filled code. Review the following code diff and determine if it's cheerful and contains sufficient emojis.

Respond with:
- PASS: if the code meets the criteria.
- FAIL: if the code lacks cheerfulness or emojis.

Provide a brief explanation.

Code Diff:
{diff}
"""

try:
    # Try to get a response from the OpenAI API
    completion = client.chat.completions.create(
        # Use the gpt-4o model for the review
        model="gpt-4o",
        # Use the system role to set the context for the LLM
        # Use the user role to provide the prompt
        messages=[
            {"role": "system", "content": "You are a cheerful code reviewer who loves emoji-filled code."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Get the content of the response
    message = completion.choices[0].message.content

except Exception as e:
    # Catch any errors from the OpenAI API
    print(f"Error communicating with OpenAI: {e}")
    sys.exit(1)

# Provide context in github actions logs
print("LLM Response:")
print(message)

# Check for PASS or FAIL in the response
# Check if the response starts with "PASS: " or "FAIL: "
# TODO: Improve the parsing with re
passed = (message and message[0:6].lower() == "pass: ")
# If the response starts with "PASS: " or "FAIL: ", remove it from the message
message = message[6:] if (message and (passed or message[0:6].lower() == "fail: ")) else message

# Step 4: Add comment to PR
# Format the request URI for the GitHub API
# github.repository is the full name of the repository in the format "owner/repo"
request_uri = f"https://api.github.com/repos/{REPO_NAME}/pulls/{PR_NUMBER}/comments"
# Set the request headers and body
# Following https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28#create-a-review-comment-for-a-pull-request
request_headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
    "Content-Type": "application/json",
}
# The body of the comment includes the LLM review result and the message
# The message is formatted to include the LLM review result and the message
request_body = {
    "body": f"## Your ✨Review✨\n\n{message}\n\n---\n\n### LLM Review Result: {'PASS' if passed else 'FAIL'}",
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