import os

# Configuration
SOURCE_DIR = r"c:\Users\armad\OneDrive\Documents\Professional\MLTS\Timeline\Fall 2025\Courses\Healthy Boundaries\Projects\Final Project"
DEST_DIR = os.path.join(SOURCE_DIR, "hb_final", "2_sources_md")

sources = [
    {
        "filename": "Dao of Complexity - Unknown.txt",
        "out_name": "Dao_of_Complexity.md",
        "frontmatter": {
            "title": "The Dao of Complexity",
            "author": "Jean Boulton",
            "year": "2024",
            "source_type": "book",
            "tags": ["complexity", "daoism", "process-philosophy", "science"]
        }
    },
    {
        "filename": "Shared Wisdom - Pamela Cooper-White.txt",
        "out_name": "Shared_Wisdom.md",
        "frontmatter": {
            "title": "Shared Wisdom: Use of the Self in Pastoral Care and Counseling",
            "author": "Pamela Cooper-White",
            "year": "2024",
            "edition": "20th Anniversary Revised",
            "source_type": "book",
            "tags": ["pastoral-care", "intersubjectivity", "transference", "psychology"]
        }
    },
    {
        "filename": "Sacred Wounds - Teresa B. Pasquale.txt",
        "out_name": "Sacred_Wounds.md",
        "frontmatter": {
            "title": "Sacred Wounds: A Path to Healing from Spiritual Trauma",
            "author": "Teresa B. Pasquale",
            "year": "2015",
            "source_type": "book",
            "tags": ["trauma", "healing", "spiritual-abuse", "ministry"]
        }
    }
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
            with open(src_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            full_content = create_frontmatter(source["frontmatter"]) + content
            
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
                
            print(f"  -> Converted to {source['out_name']} ({len(content)} chars)")
            
        except Exception as e:
            print(f"  -> ERROR: {e}")

if __name__ == "__main__":
    convert()
