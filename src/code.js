const showInstructions = () => {
  const md = fetchReadme(); // pulls from cache or network
  const html = buildMarkdownSidebar(md);
  const output = HtmlService.createHtmlOutput(html)
    .setTitle("Instructions for Use")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .setWidth(400);
  SpreadsheetApp.getUi().showSidebar(output);
};

const fetchReadme = () => {
  const cache = CacheService.getScriptCache();
  const cached = cache.get("readme_md");
  if (cached) return cached;

  // Public raw URL (no auth required for public repo)
  const url =
    "https://raw.githubusercontent.com/orangeandoliveco/orangeandoliveco.in/main/README.md";
  const res = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
  const code = res.getResponseCode();
  if (code !== 200) {
    throw new Error("Failed to fetch README.md, HTTP " + code);
  }
  const md = res.getContentText("UTF-8");
  cache.put("readme_md", md, 600); // cache for 10 minutes
  return md;
};

/**
 * Build an HTML page that renders the Markdown in a nice, readable way.
 * Uses marked.js from a CDN (client-side) to convert Markdown → HTML.
 */
const buildMarkdownSidebar = (markdown) => {
  // Extract the section required
  // Look for content wrapped in <!-- instructions-start --> and <!-- instructions-end -->
  console.log(markdown);
  const [start, end] = [
    "<!-- instructions-start -->",
    "<!-- instructions-end -->",
  ];
  if (markdown.includes(start) && markdown.includes(end)) {
    markdown = markdown.split(start)[1];
    markdown = markdown.split(end)[0];
  }
  const mdJson = JSON.stringify(markdown);
  return `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Instructions</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif; padding: 12px 14px; color: #222; }
  h1, h2, h3 { margin-top: 1.2em; }
  pre, code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
  pre { background: #f6f8fa; padding: 10px; overflow:auto; border-radius: 6px; }
  code { background: #f6f8fa; padding: 2px 4px; border-radius: 4px; }
  a { color: #0b57d0; text-decoration: none; }
  a:hover { text-decoration: underline; }
  ul, ol { padding-left: 1.4em; }
  blockquote { border-left: 4px solid #e0e0e0; margin: 0; padding: 0 10px; color: #555; }
</style>
</head>
<body>
  <div id="app">Loading…</div>

  <!-- Markdown renderer -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"crossorigin="anonymous"></script>
  <script>
    const md = ${mdJson};
    // Configure marked minimally
    marked.setOptions({
      breaks: true,
      mangle: false,   // avoid email mangling
      headerIds: true
    });
    const html = marked.parse(md);
    console.log(html, "rendered html");
    document.getElementById('app').innerHTML = html;
  </script>
</body>
</html>`;
};

const getColumnNumbers = (sheet) => {
  const headers = sheet.getDataRange().getValues()[0];
  const fileNameCol = headers.indexOf("image") + 1;
  const fileIdCol = headers.indexOf("file_id") + 1;
  return { fileNameCol, fileIdCol };
};

const onOpen = () => {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu("Website")
    .addItem("Update File IDs", "update")
    .addSeparator()
    .addItem("Help", "showInstructions")
    .addToUi();
};

const update = () => {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();

  const props = PropertiesService.getScriptProperties();
  const folderId = props.getProperty("FOLDER_ID");
  if (!folderId) {
    SpreadsheetApp.getUi().alert("Folder ID not set in script properties.");
    return;
  }
  const folder = DriveApp.getFolderById(folderId);
  const files = folder.getFiles();
  const fileMap = {};

  const { fileNameColumn, fileIdColumn } = getColumnNumbers(sheet);

  // Map file name to file object (not just ID, we need to update permissions)
  while (files.hasNext()) {
    const file = files.next();
    fileMap[file.getName()] = file;
  }

  for (let i = 1; i < data.length; i++) {
    const filename = data[i][fileNameColumn - 1];
    const range = sheet.getRange(i + 1, fileIdColumn);

    if (filename && fileMap[filename]) {
      const file = fileMap[filename];

      // Set sharing permission
      file.setSharing(
        DriveApp.Access.ANYONE_WITH_LINK,
        DriveApp.Permission.VIEW,
      );

      // Insert file ID
      range.setValue(file.getId());
    } else if (filename) {
      range.setValue("❌ Not Found");
    }
  }
};
