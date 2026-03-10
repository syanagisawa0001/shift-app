function doGet(e) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const userSheet = ss.getSheetByName("users");
  
  // 対象月の決定 (例: 2026-04)。エディタから直接実行された場合は e が undefined になるため保護する
  const targetMonthStr = (e && e.parameter && e.parameter.target_month) ? e.parameter.target_month : null;
  
  // 全シートから「YYYY-MM」形式の月リストを取得
  const allSheets = ss.getSheets();
  const regex = /^\d{4}-\d{2}$/;
  let availableMonths = [];
  let defaultSheet = null;
  
  for (let i = 0; i < allSheets.length; i++) {
    const sName = allSheets[i].getName();
    if (regex.test(sName)) {
      availableMonths.push(sName);
    }
    // "shifts" や "シフト" という古い形式のシートがあればそれも確保しておく
    if (sName === "shifts" || sName === "シフト") {
      if(!defaultSheet) defaultSheet = allSheets[i];
    }
  }
  availableMonths.sort().reverse(); // 新しい月を上に
  
  let targetSheet = null;
  
  if (targetMonthStr && regex.test(targetMonthStr)) {
    targetSheet = ss.getSheetByName(targetMonthStr);
    
    // 指定された月のシートが存在しない場合、新規作成する
    if (!targetSheet) {
      targetSheet = createNewMonthSheet(ss, targetMonthStr, defaultSheet || allSheets[0]);
      availableMonths.push(targetMonthStr);
      availableMonths.sort().reverse();
    }
  } else {
    // target_monthが指定されていない場合は、最新の月シートか、デフォルトシートを返す
    targetSheet = availableMonths.length > 0 ? ss.getSheetByName(availableMonths[0]) : (defaultSheet || allSheets[0]);
  }
  
  const currentMonthName = targetSheet.getName();

  // 1. シフト・日付データの取得
  const shiftValues = targetSheet.getDataRange().getDisplayValues();
  // ヘッダー行をトリムして取得
  const dateHeaders = shiftValues.length > 0 ? shiftValues[0].slice(1).map(h => h.trim()) : [];
  
  // 2. ユーザー認証データの取得
  let userList = [];
  if (userSheet) {
    const userData = userSheet.getDataRange().getDisplayValues();
    for (let i = 1; i < userData.length; i++) {
      if (userData[i][0]) {
        userList.push({
          username: userData[i][0].trim(),
          pin: userData[i][1].trim()
        });
      }
    }
  }

  // 3. 全シフトデータの整形 (My Shift表示用)
  const allShiftData = {};
  for (let i = 1; i < shiftValues.length; i++) {
    const row = shiftValues[i];
    const staffName = row[0] ? row[0].trim() : "";
    if (staffName) {
      allShiftData[staffName] = {};
      for (let j = 1; j < row.length; j++) {
        const dateLabel = shiftValues[0][j] ? shiftValues[0][j].trim() : "";
        if (dateLabel) {
          allShiftData[staffName][dateLabel] = row[j];
        }
      }
    }
  }
  
  return ContentService.createTextOutput(JSON.stringify({
    current_month: currentMonthName,
    available_months: availableMonths,
    date_headers: dateHeaders,
    users: userList,
    all_shift_data: allShiftData,
    debug_info: {
      sheet_name: targetSheet.getName(),
      row_count: shiftValues.length,
      col_count: shiftValues[0] ? shiftValues[0].length : 0
    }
  })).setMimeType(ContentService.MimeType.JSON);
}

// 新しい月のシートを自動生成するヘルパー関数
function createNewMonthSheet(ss, monthStr, baseSheet) {
  const newSheet = ss.insertSheet(monthStr);
  
  // YYYY-MM から月末日を計算
  const parts = monthStr.split('-');
  const year = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10);
  const lastDay = new Date(year, month, 0).getDate(); // 0を指定すると前月の末日になるため、monthはそのまま(1-12)で翌月の0日=今月末日となる
  
  // 1行目（ヘッダー）の作成
  const headers = ["Staff Name"];
  for (let d = 1; d <= lastDay; d++) {
    headers.push(`${month}/${d}`); // 例: "4/1"
  }
  newSheet.appendRow(headers);
  
  // 既存スタッフ名のコピー (baseSheetが存在すればそこから取得)
  if (baseSheet) {
    const baseData = baseSheet.getDataRange().getValues();
    if (baseData.length > 1) {
      const staffNames = [];
      for (let i = 1; i < baseData.length; i++) {
        if (baseData[i][0]) staffNames.push([baseData[i][0]]);
      }
      if (staffNames.length > 0) {
        newSheet.getRange(2, 1, staffNames.length, 1).setValues(staffNames);
      }
    }
  }
  return newSheet;
}

function doPost(e) {
  try {
    const params = JSON.parse(e.postData.contents);
    const type = params.type; 
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    
    if (type === "signup") {
      return handleSignUp(params, ss);
    } else {
      return handleUpdate(params, ss);
    }
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({success: false, message: "JSON解析エラー: " + err.message})).setMimeType(ContentService.MimeType.JSON);
  }
}

function handleSignUp(params, ss) {
  const username = params.username.trim();
  const pin = params.pin.trim();
  
  let userSheet = ss.getSheetByName("users");
  if (!userSheet) {
    userSheet = ss.insertSheet("users");
    userSheet.appendRow(["username", "pin"]);
  }
  
  // 重複チェック
  const lastRow = userSheet.getLastRow();
  const existingUsers = lastRow > 0 ? userSheet.getRange(1, 1, lastRow, 1).getValues().flat().map(u => String(u).trim()) : [];
  if (existingUsers.includes(username)) {
    return ContentService.createTextOutput(JSON.stringify({success: false, message: "この名前は既に登録されています"})).setMimeType(ContentService.MimeType.JSON);
  }
  
  userSheet.appendRow([username, pin]);
  
  // 全ての月シート(YYYY-MM)にスタッフ名を追加
  const allSheets = ss.getSheets();
  const regex = /^\d{4}-\d{2}$/;
  for (let i = 0; i < allSheets.length; i++) {
    const sName = allSheets[i].getName();
    if (regex.test(sName) || sName === "shifts" || sName === "シフト") {
      allSheets[i].appendRow([username]);
    }
  }
  
  return ContentService.createTextOutput(JSON.stringify({success: true, message: "登録完了"})).setMimeType(ContentService.MimeType.JSON);
}

function handleUpdate(params, ss) {
  const staffName = params.staff_name.trim();
  const updates = params.updates; 
  const targetMonthStr = params.target_month; // 例: "2026-04"
  
  let sheet = null;
  if (targetMonthStr) {
    sheet = ss.getSheetByName(targetMonthStr);
  }
  // 指定がない、または見つからない場合はフォールバック
  if (!sheet) {
    sheet = ss.getSheetByName("shifts") || ss.getSheetByName("シフト") || ss.getSheets()[0];
  }
  
  const fullRange = sheet.getDataRange().getDisplayValues();
  const headers = fullRange[0].map(h => h.trim());
  const staffNames = fullRange.map(row => row[0].trim());
  
  let rowIndex = staffNames.indexOf(staffName) + 1;
  
  if (rowIndex === 0) {
    return ContentService.createTextOutput(JSON.stringify({
      success: false, 
      message: "スタッフが見つかりません: " + staffName,
      debug: { staff_list: staffNames.slice(0, 10) }
    })).setMimeType(ContentService.MimeType.JSON);
  }
  
  let successDates = [];
  let failedDates = [];
  
  // 一括更新を効率化
  updates.forEach(update => {
    const targetDate = update.date_label.trim();
    const colIndex = headers.indexOf(targetDate) + 1;
    
    if (colIndex > 0) {
      sheet.getRange(rowIndex, colIndex).setValue(update.shift_value);
      successDates.push(targetDate);
    } else {
      failedDates.push(targetDate);
    }
  });
  
  return ContentService.createTextOutput(JSON.stringify({
    success: successDates.length > 0,
    success_count: successDates.length,
    failed_count: failedDates.length,
    success_dates: successDates,
    failed_dates: failedDates,
    message: successDates.length > 0 ? "更新完了" : "一致する日付が見つかりませんでした"
  })).setMimeType(ContentService.MimeType.JSON);
}
