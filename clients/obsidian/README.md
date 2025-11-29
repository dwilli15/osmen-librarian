# Librarian for Obsidian

This script allows you to query your local Librarian Agent directly from Obsidian.

## Setup

1.  **Install QuickAdd Plugin**:
    - Open Obsidian Settings > Community Plugins > Browse > Search "QuickAdd" > Install & Enable.

2.  **Install Script**:
    - Copy `librarian_connector.js` to your vault's script folder (e.g., `Scripts/librarian_connector.js`).
    - *Note*: You may need to create a folder for scripts and tell QuickAdd where it is in Settings.

3.  **Configure Path**:
    - Open `librarian_connector.js` in a text editor.
    - Update `LIBRARIAN_PATH` to point to your `librarian_repo` location.
      ```javascript
      const LIBRARIAN_PATH = "D:/path/to/librarian_repo";
      ```

4.  **Create Macro**:
    - Open QuickAdd Settings > Manage Macros.
    - Name: "Ask Librarian".
    - Add "User Script" step -> Select `librarian_connector`.

5.  **Add Command**:
    - Go back to QuickAdd main menu.
    - Add "Macro" choice -> Select "Ask Librarian".
    - Click the lightning bolt to add it to the Command Palette.

## Usage
1.  Open Command Palette (`Ctrl/Cmd + P`).
2.  Run "QuickAdd: Ask Librarian".
3.  Type your question.
4.  Select mode (Foundation, Lateral, Fact Check).
5.  Wait for the insight to be inserted into your note!
