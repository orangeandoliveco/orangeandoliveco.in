const getColumnNumbers = (sheet) => {
  const headers = sheet.getDataRange().getValues()[0];
  const fileNameCol = headers.indexOf("image") + 1;
  const fileIdCol = headers.indexOf("file_id") + 1;
  return { fileNameCol, fileIdCol };
};

const onOpen = () => {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu("Website").addItem("Update File IDs", "update").addToUi();
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
