import os
import re

# from datetime import date, timedelta
from typing import Dict

from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from github import GitHubAPI, GitHubAPIException
from utils import language_options

# process_before_response must be True when running on FaaS
app = App(process_before_response=True)

GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
gh = GitHubAPI(token=GITHUB_API_KEY)

# def next_issue_date():
#     today = date.today()
#     if today.weekday() == 3:
#         return today
#     dt = today + timedelta((3 - today.weekday()) % 7)
#     return dt


newsletter_categories = [
    "Releases",
    "Backend",
    "Frontend",
    "DevOps",
    "Machine Learning",
    "Tooling",
    "In other news",
]
newsletter_schema = f""
for cat in newsletter_categories:
    newsletter_schema += f"---\n## {cat}\n\n"


def get_digest_issue_body(owner, repo, issue_number):
    try:
        req = gh.get(f"/repos/{owner}/{repo}/issues/{issue_number}")
    except GitHubAPIException:
        pass
    return req["body"]


def create_new_digest_issue(owner, repo, body):
    try:
        params = {"title": "[PLACEHOLDER]", "body": body, "labels": ["newsletter"]}
        req = gh.post(f"/repos/{owner}/{repo}/issues", **params)
        issue_number = req["number"]
    except GitHubAPIException as err:
        print(err)

    return issue_number


def update_digest_issue(owner, repo, issue_number, body):
    try:
        params = {"body": body}
        gh.patch(f"/repos/{owner}/{repo}/issues/{issue_number}", **params)
    except GitHubAPIException as err:
        print(err)


def find_or_create_digest_issue(owner, repo, default_body):
    q = f"repo:{owner}/{repo} is:open is:issue label:newsletter"

    params = {"q": q}
    try:
        req = gh.get("/search/issues", **params)
    except GitHubAPIException as err:
        print(err)

    res = req["total_count"]

    if res == 1:
        draft = req["items"][0]
        issue_number = draft["number"]
    else:
        # create an issue
        issue_number = create_new_digest_issue(owner, repo, default_body)

    return issue_number


@app.message(":wave:")
def say_hello(message, say):
    user = message["user"]
    say(f"Hi there, <@{user}>! Do you like newsletters? I do.")


# @app.command("/buttondown")
# Listen for a shortcut invocation
@app.shortcut("add_content")
def open_modal(ack, body, client):
    print("modal ", body)
    user = body["user"]["username"]
    channel = body["channel"]["id"]
    msg = body["message"]
    msg_ts = msg["ts"]
    title = ""
    title_link = ""
    image_link = ""
    summary = ""

    try:
        attachments = msg["attachments"][0]
    except (KeyError, IndexError):
        attachments = None

    if attachments:
        # github repo
        try:
            if attachments["app_unfurl_url"].startswith("https://github.com/"):
                title_link = attachments["app_unfurl_url"]
        except KeyError:
            pass

        image_link = attachments.get("image_url", None)

        if not title_link:
            title_link = attachments.get("title_link", "")

        title = attachments.get("title", "")
        summary = attachments.get("text", "")

    else:
        title = msg["text"]
        try:
            title_link = msg["blocks"][0]["elements"][0]["elements"][0]["url"]
        except (KeyError, IndexError):
            pass

    # View payload
    view = {
        "type": "modal",
        # View identifier
        "callback_id": "add_content_view",
        "title": {"type": "plain_text", "text": "Add Content"},
        "submit": {"type": "plain_text", "text": "Add"},
        "blocks": [
            {
                "type": "input",
                "block_id": "content_title",
                "element": {
                    "initial_value": title,
                    "type": "plain_text_input",
                    "action_id": "title_input",
                },
                "label": {"type": "plain_text", "text": "Link title", "emoji": True},
            },
            {
                "type": "input",
                "element": {
                    "initial_value": title_link,
                    "type": "plain_text_input",
                    "action_id": "link_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Placeholder text for single-line input",
                    },
                },
                "label": {"type": "plain_text", "text": "Link"},
                "hint": {"type": "plain_text", "text": "Hint text"},
            },
            {
                "type": "input",
                "optional": True,
                "element": {
                    "initial_value": summary,
                    "type": "plain_text_input",
                    "action_id": "summary_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Text here will be displayed as a markdown formatted blockquote.",
                    },
                },
                "label": {"type": "plain_text", "text": "Additional content"},
                "hint": {"type": "plain_text", "text": "Hint text"},
            },
            {
                "type": "input",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an item",
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": f"{cat}",
                                "emoji": True,
                            },
                            "value": f"{cat}",
                        }
                        for cat in newsletter_categories
                    ],
                    "action_id": "category_input",
                },
                "label": {"type": "plain_text", "text": "Category", "emoji": True},
            },
            {
                "type": "input",
                "optional": True,
                "element": {
                    "type": "multi_static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select languages and frameworks",
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": f"{lang}",
                                "emoji": True,
                            },
                            "value": f"{lang}",
                        }
                        for lang in language_options
                    ],
                    "action_id": "langs_input",
                },
                "label": {
                    "type": "plain_text",
                    "text": "Languages & frameworks",
                    "emoji": True,
                },
            },
            {
                "type": "input",
                "element": {
                    "initial_value": f"{channel}/{msg_ts}",
                    "type": "plain_text_input",
                    "action_id": "ref_msg",
                },
                "label": {"type": "plain_text", "text": "Msg Ref"},
                "hint": {"type": "plain_text", "text": "Don't Edit!"},
            },
        ],
    }

    if image_link:
        img_blocks = [
            {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": "Image from link",
                    "emoji": True,
                },
                "image_url": f"{image_link}",
                "alt_text": "image from site",
            },
            {
                "type": "input",
                "optional": True,
                "element": {
                    "type": "checkboxes",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Include this image?",
                                "emoji": True,
                            },
                            "value": "True",
                        }
                    ],
                    "action_id": "include_image_input",
                },
                "label": {"type": "plain_text", "text": "Label", "emoji": True},
            },
        ]

        img_ref = {
            "type": "input",
            "element": {
                "initial_value": f"{image_link}",
                "type": "plain_text_input",
                "action_id": "ref_img",
            },
            "label": {"type": "plain_text", "text": "Image Ref"},
            "hint": {"type": "plain_text", "text": "Don't Edit!"},
        }

        view["blocks"] = view["blocks"][:3] + img_blocks + view["blocks"][3:]
        view["blocks"] += [img_ref]

    # Acknowledge the command request
    ack()

    # Call views_open with the built-in client
    # Pass a valid trigger_id within 3 seconds of receiving it
    client.views_open(trigger_id=body["trigger_id"], view=view)


def add_md_to_category(body: str, md: str, category: str) -> str:
    r = f"## {category}.*?##"
    section = re.compile(r, re.DOTALL)
    match = section.search(body)
    if match:
        end = match.end() - 2
        body = body[:end] + md + body[end:]
    else:
        # simple append
        body = body + md

    return body


# embeds
def is_embed(txt: str) -> bool:
    txt = txt.strip()
    return (
        txt.startswith("https://twitter.com")
        or txt.startswith("https://www.twitter.com")
        or txt.startswith("https://github.com/")
        or txt.startswith("https://www.github.com/")
        or txt.startswith("https://www.youtube.com/")
        or txt.startswith("https://youtube.com/")
    )


def rec_to_md(rec: Dict) -> str:
    title = rec["title_input"]

    link = rec["link_input"]
    if link.endswith("?s=12"):
        link = link[:-5]

    include_img = rec.get("include_image_input", None)
    img_link = rec.get("ref_img", None)

    summary = rec["summary_input"]
    category = rec["category_input"]

    langs = rec.get("langs_input", [])

    site = ""
    if link.startswith("https://github.com/") or link.startswith(
        "https://www.github.com/"
    ):
        site = "GitHub - "

    md = f"### [{site}{title}]({link})\n"

    if include_img:
        md += f"![]({img_link})\n\n"

    md += f'<span class="category">`{category}` </span>'

    for lang in langs:
        if lang != "None":
            md += f'<span class="{lang}">`{lang}` </span>'

    md += "\n"

    if is_embed(link):
        md += f"\n{link}\n\n"

    if summary:
        if is_embed(summary):
            md += f"{summary}\n\n"
        else:
            md += f"> {summary}\n\n"
    else:
        md += "\n\n"

    md += "---\n"

    return md


@app.view("add_content_view")
def handle_view_submission(ack, body, client, view, logger):

    state = view["state"]
    print("state ", state)

    rec = {}
    for o in state["values"].values():
        for k, v in o.items():
            if v["type"] == "plain_text_input":
                val = v["value"]

            elif v["type"] == "static_select":
                val = v["selected_option"]["value"]

            elif v["type"] == "multi_static_select":
                opts = v.get("selected_options", None)
                if opts:
                    val = [opt["value"] for opt in opts]
                else:
                    continue

            elif v["type"] == "checkboxes":
                check = v.get("selected_options", None)
                if check:
                    val = True
                else:
                    # don't include image
                    continue

            rec[k] = val

    print("record ", rec)

    ref_msg = rec["ref_msg"].split("/")
    channel = ref_msg[0]
    msg_ts = ref_msg[1]

    # restrict duplicate content
    # by checking to see if the app (buttondown)
    # has not reacted to the message already
    msg_reactions = app.client.reactions_get(
        channel=channel,
        timestamp=msg_ts,
    )

    errors = {}
    try:
        reactions = msg_reactions["message"]["reactions"]
    except KeyError:
        reactions = None

    if reactions:
        for it in reactions:
            if it["name"] == "heavy_check_mark" and "U021CN80RV1" in it["users"]:
                print("content already added...")
                errors[
                    "content_title"
                ] = "This content has already been added to an issue."
                ack(response_action="errors", errors=errors)
                return

    # continue
    ack()

    # update draft
    # find or create draft
    owner = "siegerts"
    repo = "fullstackdigest"

    # TODO: break this out
    issue_number = find_or_create_digest_issue(owner, repo, newsletter_schema)
    # get issue body
    issue_body = get_digest_issue_body(owner, repo, issue_number)

    # update content
    # TODO: enhance this
    category = rec["category_input"]
    md = rec_to_md(rec)
    body = add_md_to_category(issue_body, md, category)

    # update issue
    update_digest_issue(owner, repo, issue_number, body)

    # add reaction to message
    app.client.reactions_add(
        channel=channel,
        name="heavy_check_mark",
        timestamp=msg_ts,
    )


def handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
