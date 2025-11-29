import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
ROOT_PAGE_ID = os.getenv("NOTION_PAGE_ID")
OUTPUT_DIR = "../../data/notion"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_page_title(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        # Try to find title in properties (schema varies)
        for prop in data["properties"].values():
            if prop["type"] == "title":
                return prop["title"][0]["plain_text"]
    return "Untitled"

def get_blocks(block_id):
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def blocks_to_markdown(blocks):
    md = ""
    for block in blocks:
        btype = block["type"]
        if btype == "paragraph":
            text = "".join([t["plain_text"] for t in block["paragraph"]["rich_text"]])
            md += f"{text}\n\n"
        elif btype == "heading_1":
            text = "".join([t["plain_text"] for t in block["heading_1"]["rich_text"]])
            md += f"# {text}\n\n"
        elif btype == "heading_2":
            text = "".join([t["plain_text"] for t in block["heading_2"]["rich_text"]])
            md += f"## {text}\n\n"
        elif btype == "bulleted_list_item":
            text = "".join([t["plain_text"] for t in block["bulleted_list_item"]["rich_text"]])
            md += f"- {text}\n"
    return md

def sync_page(page_id):
    print(f"Syncing page {page_id}...")
    title = get_page_title(page_id)
    blocks = get_blocks(page_id)
    content = blocks_to_markdown(blocks)
    
    filename = f"{title.replace(' ', '_')}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved to {filepath}")

if __name__ == "__main__":
    if not NOTION_API_KEY or not ROOT_PAGE_ID:
        print("Error: NOTION_API_KEY and NOTION_PAGE_ID must be set in .env")
    else:
        sync_page(ROOT_PAGE_ID)
