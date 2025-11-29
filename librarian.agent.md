# Librarian Agent Plan

## Project Goals
The "Librarian" project aims to create a sophisticated RAG (Retrieval-Augmented Generation) system for managing and querying a knowledge base of academic and therapeutic resources. It serves as a dedicated repository and processing engine, separate from the initial "Final Project" prototype.

## Core Features
1.  **RAG Engine**: A robust backend for indexing and retrieving context from markdown and text documents.
2.  **Deep Analysis**: Tools for analyzing document structure and content (e.g., `deep_analyzer.py`).
3.  **Obsidian Integration**: Future integration to allow Obsidian to act as a frontend UI for the RAG system, enabling "chat with your notes" functionality.
4.  **API Interface**: Exposing the RAG capabilities via a local API for external tools.

## Migration Manifest
This project is initialized by migrating core tools and data from the "Healthy Boundaries Final Project".

### Tools (Migrated to `src/`)
- `rag_manager.py`: Core logic for the RAG system.
- `deep_analyzer.py`: Utility for deep content analysis.

### Data (Migrated to `data/`)
- **Sources**:
    - `Cortina_Liotti.md`
    - `Dao_of_Complexity.md`
    - `Gillespie_Cornish.md`
    - `Sacred_Wounds.md`
    - `Shared_Wisdom.md`
- **Admin**:
    - `F25 HB Syllabus_Final.md`

## Architecture
- **Language**: Python
- **Environment**: Local `.venv`
- **Structure**:
    - `src/`: Source code and scripts.
    - `data/`: Knowledge base documents.
    - `docs/`: Documentation and planning.

## Future Work: Obsidian Integration
- Explore "OpenNotebook" or similar plugins.
- Design a local REST API (FastAPI/Flask) that Obsidian plugins can query.
