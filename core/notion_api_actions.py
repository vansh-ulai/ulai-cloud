import os
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Notion API client
notion = Client(auth=os.getenv("NOTION_TOKEN"))

async def create_new_page(title: str, parent_page_id: str):
    """Creates a new Notion page under a parent page."""
    try:
        response = notion.pages.create(
            parent={"page_id": parent_page_id},
            properties={
                "title": [
                    {
                        "text": {"content": title}
                    }
                ]
            }
        )
        print(f"✅ Created page '{title}' successfully.")
        return response
    except Exception as e:
        print(f"❌ Error creating page: {e}")
        return None


async def add_paragraph(page_id: str, text: str):
    """Adds a paragraph block to a Notion page."""
    try:
        response = notion.blocks.children.append(
            page_id,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": text}}
                        ]
                    },
                }
            ],
        )
        print(f"✅ Added paragraph: '{text}'")
        return response
    except Exception as e:
        print(f"❌ Error adding paragraph: {e}")
        return None
