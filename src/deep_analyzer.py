import os
import yaml
import glob
from langchain_core.documents import Document
from lateral_thinking import LateralEngine

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../hb_final"))
INDEX_FILE = os.path.join(ROOT_DIR, "0_admin/file-index.md")

def get_frontmatter(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.startswith('---'):
                end = content.find('---', 3)
                if end != -1:
                    fm = content[3:end]
                    return yaml.safe_load(fm)
    except Exception:
        pass
    return {}

def generate_tree(start_path, prefix=""):
    tree_str = ""
    contents = sorted(os.listdir(start_path))
    pointers = [("├── ", "│   ")] * (len(contents) - 1) + [("└── ", "    ")]
    
    for pointer, path in zip(pointers, contents):
        full_path = os.path.join(start_path, path)
        name = path
        
        if os.path.isdir(full_path):
            tree_str += f"{prefix}{pointer[0]}{name}/\n"
            tree_str += generate_tree(full_path, prefix + pointer[1])
        else:
            tree_str += f"{prefix}{pointer[0]}{name}\n"
            
    return tree_str

def analyze_workspace():
    print(f"Analyzing {ROOT_DIR}...")
    
    # Generate Tree
    tree = generate_tree(ROOT_DIR)
    
    # Index Files
    index_content = f"# Workspace Index\n\n## Directory Structure\n```\n{tree}```\n\n## File Index\n"
    
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, ROOT_DIR)
                fm = get_frontmatter(path)
                
                title = fm.get('title', file)
                tags = fm.get('tags', [])
                if isinstance(tags, list):
                    tags_str = ", ".join(tags)
                else:
                    tags_str = str(tags)
                
                index_content += f"\n### [{title}]({rel_path})\n"
                index_content += f"- **Path**: `{rel_path}`\n"
                if tags_str:
                    index_content += f"- **Tags**: {tags_str}\n"
                
                # Lateral Enrichment
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    doc = Document(page_content=content)
                    lateral_engine = LateralEngine()
                    enriched_doc = lateral_engine.enrich_document(doc)
                    c7_meta = {k: v for k, v in enriched_doc.metadata.items() if k.startswith('c7_')}
                    if c7_meta:
                        index_content += f"- **Context7**: {c7_meta}\n"
                except Exception as e:
                    print(f"Error enriching {file}: {e}")
                
                # Lateral Enrichment
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    doc = Document(page_content=content)
                    lateral_engine = LateralEngine()
                    enriched_doc = lateral_engine.enrich_document(doc)
                    c7_meta = {k: v for k, v in enriched_doc.metadata.items() if k.startswith('c7_')}
                    if c7_meta:
                        index_content += f"- **Context7**: {c7_meta}\n"
                except Exception as e:
                    print(f"Error enriching {file}: {e}")
                
                # Add summary or first few lines?
                # For now, just metadata
                
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(index_content)
    
    print(f"Index generated at {INDEX_FILE}")

if __name__ == "__main__":
    analyze_workspace()
