# slack-github-newsletter-shortcut

## Overview

`slack-github-newsletter-shortcut` is a Python utility application designed to integrate Slack with GitHub for creating and managing a newsletter digest. It allows users to easily add content to a GitHub issue (serving as a newsletter draft) directly from Slack using a shortcut. The application automates the process of drafting a newsletter by collecting and organizing contributions from Slack into a structured format.

## Features

- **Slack Shortcut Integration**: Users can add content to the newsletter using a Slack shortcut.
- **GitHub Issue Management**: The application creates and updates a GitHub issue to serve as the newsletter draft.
- **Content Categorization**: Users can categorize their contributions into predefined categories like Releases, Backend, Frontend, DevOps, etc.
- **Markdown Formatting**: Contributions are automatically formatted in Markdown.
- **Duplicate Content Check**: The application checks for and avoids duplicate content entries.

## Requirements

- Python 3.x
- Slack workspace with admin privileges to install apps
- GitHub account and repository for hosting the newsletter
- Environment variables:
  - `GITHUB_API_KEY`: A GitHub API token with permissions to access the repository
  - `SLACK_BOT_TOKEN`: Your Slack Bot Token
  - `SLACK_SIGNING_SECRET`: Your Slack App's Signing Secret

## Installation

Clone the repository:

bash

1. Copy code

```
git clone https://github.com/your-username/slack-github-newsletter-shortcut.git
```

2. Install dependencies

```
pip install -r requirements.txt
```

3. Set up the necessary environment variables, including `GITHUB_API_KEY`, `SLACK_BOT_TOKEN`, and `SLACK_SIGNING_SECRET`.

4. Deploy the application to a server or a cloud function (like AWS Lambda) that supports Python.

5. Configure a Slack app and point it to your deployment.

## Usage

1. Adding Content via Slack:

- Use the /add_content shortcut in Slack to open a modal.
- Fill in the details about the content you want to add (title, link, summary, category, etc.).
- Submit the form to add the content to the GitHub issue.

2. Managing the Newsletter Draft:

- The application will automatically create a new GitHub issue or update an existing one in the specified repository.
- The issue will be updated with the content submitted from Slack, formatted in Markdown.

## License

This project is licensed under the MIT License.
