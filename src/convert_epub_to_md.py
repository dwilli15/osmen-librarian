import zipfile
import xml.etree.ElementTree as ET
import sys
import os
import re

def epub_to_markdown(epub_path, md_path):
    """
    Converts an .epub file to a simple markdown file by extracting text from XHTML content.
    """
    try:
        if not os.path.exists(epub_path):
            print(f"Error: File not found at {epub_path}")
            return

        markdown_lines = []
        
        # Open the .epub file as a zip file
        with zipfile.ZipFile(epub_path) as zf:
            # Find the OPF file to get the reading order
            container_xml = zf.read('META-INF/container.xml')
            container_tree = ET.fromstring(container_xml)
            rootfile_path = container_tree.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile').get('full-path')
            
            opf_content = zf.read(rootfile_path)
            opf_tree = ET.fromstring(opf_content)
            
            # Namespaces in OPF
            namespaces = {
                'opf': 'http://www.idpf.org/2007/opf',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            # Get the manifest items (id -> href)
            manifest = {}
            for item in opf_tree.findall('.//opf:item', namespaces):
                manifest[item.get('id')] = item.get('href')
            
            # Get the spine (reading order)
            spine_ids = []
            for itemref in opf_tree.findall('.//opf:itemref', namespaces):
                spine_ids.append(itemref.get('idref'))
            
            # Iterate through spine items
            base_dir = os.path.dirname(rootfile_path)
            
            for item_id in spine_ids:
                if item_id in manifest:
                    href = manifest[item_id]
                    file_path = os.path.join(base_dir, href).replace('\\', '/')
                    
                    try:
                        content = zf.read(file_path).decode('utf-8')
                        
                        # Simple HTML to Markdown conversion (very basic)
                        # Remove scripts and styles
                        content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)
                        content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL)
                        
                        # Extract body content
                        body_match = re.search(r'<body.*?>(.*?)</body>', content, flags=re.DOTALL)
                        if body_match:
                            body_content = body_match.group(1)
                            
                            # Replace headers
                            body_content = re.sub(r'<h1.*?>(.*?)</h1>', r'# \1\n', body_content)
                            body_content = re.sub(r'<h2.*?>(.*?)</h2>', r'## \1\n', body_content)
                            body_content = re.sub(r'<h3.*?>(.*?)</h3>', r'### \1\n', body_content)
                            
                            # Replace paragraphs
                            body_content = re.sub(r'<p.*?>(.*?)</p>', r'\1\n\n', body_content)
                            
                            # Remove other tags
                            body_content = re.sub(r'<[^>]+>', '', body_content)
                            
                            # Unescape HTML entities (basic)
                            body_content = body_content.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                            
                            markdown_lines.append(body_content.strip())
                            markdown_lines.append('\n---\n') # Separator between chapters
                            
                    except Exception as e:
                        print(f"Warning: Could not process {file_path}: {e}")

        # Write to markdown file
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_lines))
        
        print(f"Successfully converted {epub_path} to {md_path}")

    except Exception as e:
        print(f"Error converting file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_epub_to_md.py <input_epub> <output_md>")
    else:
        epub_to_markdown(sys.argv[1], sys.argv[2])
