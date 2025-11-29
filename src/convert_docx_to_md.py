import zipfile
import xml.etree.ElementTree as ET
import sys
import os

def docx_to_markdown(docx_path, md_path):
    """
    Converts a .docx file to a simple markdown file by extracting text from XML.
    """
    try:
        if not os.path.exists(docx_path):
            print(f"Error: File not found at {docx_path}")
            return

        # Open the .docx file as a zip file
        with zipfile.ZipFile(docx_path) as zf:
            # Read the document XML
            xml_content = zf.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # Namespaces in docx XML
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            }

            markdown_lines = []
            
            # Iterate through paragraphs
            for p in tree.iterfind('.//w:p', namespaces):
                texts = []
                # Check for heading style (very basic check)
                style_node = p.find('.//w:pPr/w:pStyle', namespaces)
                is_heading = False
                heading_level = 0
                
                if style_node is not None:
                    val = style_node.get(f"{{{namespaces['w']}}}val")
                    if val and val.startswith('Heading'):
                        try:
                            heading_level = int(val.replace('Heading', ''))
                            is_heading = True
                        except ValueError:
                            pass
                
                # Extract text from runs
                for t in p.iterfind('.//w:t', namespaces):
                    if t.text:
                        texts.append(t.text)
                
                if texts:
                    line = ''.join(texts)
                    if is_heading:
                        line = '#' * heading_level + ' ' + line
                    markdown_lines.append(line)
                    markdown_lines.append('') # Add blank line between paragraphs

        # Write to markdown file
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_lines))
        
        print(f"Successfully converted {docx_path} to {md_path}")

    except Exception as e:
        print(f"Error converting file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_docx_to_md.py <input_docx> <output_md>")
    else:
        docx_to_markdown(sys.argv[1], sys.argv[2])
