import os

# Configuration - UPDATE THESE PATHS for your environment
SOURCE_DIR = os.environ.get("LIBRARIAN_SOURCE_DIR", "./source_documents")
DEST_DIR = os.environ.get("LIBRARIAN_DEST_DIR", "./data")

# Example source configuration - customize for your documents
sources = [
    {
        "filename": "example_document.txt",
        "out_name": "Example_Document.md",
        "frontmatter": {
            "title": "Example Document",
            "author": "Author Name",
            "year": "2024",
            "source_type": "book",
            "tags": ["example", "template"],
        },
    },
    # Add your sources here following the pattern above
]


def create_frontmatter(metadata):
    fm = "---\n"
    for key, value in metadata.items():
        fm += f"{key}: {value}\n"
    fm += "---\n\n"
    return fm


def convert():
    print(f"Starting conversion to {DEST_DIR}...")

    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print(f"Created directory: {DEST_DIR}")

    for source in sources:
        src_path = os.path.join(SOURCE_DIR, source["filename"])
        dest_path = os.path.join(DEST_DIR, source["out_name"])

        print(f"Processing {source['filename']}...")

        try:
            with open(src_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            full_content = create_frontmatter(source["frontmatter"]) + content

            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(full_content)

            print(f"  -> Converted to {source['out_name']} ({len(content)} chars)")

        except Exception as e:
            print(f"  -> ERROR: {e}")


if __name__ == "__main__":
    convert()
