/**
 * Librarian Connector for Obsidian
 *
 * Usage:
 * 1. Install "Templater" or "QuickAdd" plugin in Obsidian.
 * 2. Place this script in your Obsidian scripts folder.
 * 3. Configure the `LIBRARIAN_PATH` below to point to your librarian_repo.
 */

const LIBRARIAN_PATH = "D:/temp/Repo_Staging/librarian/librarian_repo"; // UPDATE THIS PATH
const PYTHON_CMD = `${LIBRARIAN_PATH}/.venv/Scripts/python.exe`;
const SCRIPT_PATH = `${LIBRARIAN_PATH}/src/rag_manager.py`;

module.exports = async (params) => {
  const quickAddApi = params; // If using QuickAdd

  // 1. Get Query from User
  let query = await quickAddApi.inputPrompt("Ask the Librarian:");
  if (!query) return;

  // 2. Select Mode
  const mode = await quickAddApi.suggester(
    [
      "Foundation (Basic Concepts)",
      "Lateral (Creative Links)",
      "Fact Check (Evidence)",
    ],
    ["foundation", "lateral", "factcheck"]
  );
  if (!mode) return;

  // 3. Execute Python Script
  const { exec } = require("child_process");

  new Notice(`Librarian is thinking... (${mode})`);

  const command = `"${PYTHON_CMD}" "${SCRIPT_PATH}" query "${query}" --mode ${mode}`;

  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) {
        new Notice(`Error: ${error.message}`);
        resolve(`Error querying Librarian: ${error.message}`);
        return;
      }
      if (stderr) {
        console.warn(`Librarian Stderr: ${stderr}`);
      }

      try {
        // Parse JSON output
        const results = JSON.parse(stdout);
        let markdownOutput = `### Librarian Response: "${query}"\n\n`;

        results.forEach((doc, index) => {
          const layer = doc.metadata.retrieval_layer
            ? `(${doc.metadata.retrieval_layer})`
            : "";
          markdownOutput += `#### Source ${index + 1} ${layer}\n`;
          markdownOutput += `> ${doc.content}\n`;
          markdownOutput += `*Source: ${doc.metadata.source}*\n\n`;
        });

        resolve(markdownOutput);
      } catch (e) {
        resolve(`Error parsing response: ${e.message}\nRaw output: ${stdout}`);
      }
    });
  });
};
