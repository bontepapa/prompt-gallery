# 🚀 프롬프트 갤러리 백엔드(구글 드라이브) 세팅 가이드

클라우드 갤러리를 만들기 위해 짦은 코드를 하나 복사/붙여넣기 해야 합니다. 딱 한 번만 하시면 평생 동작합니다! 차근차근 따라와 주세요.

---

## 1단계: 구글 스프레드시트 만들기
1. 구글 드라이브의 새로 만드신 **`image prompt data`** 폴더 안으로 들어갑니다.
2. 폴더 안에서 마우스 우클릭 -> **[Google 스프레드시트]** -> **[빈 스프레드시트]**를 생성합니다.
3. 시트의 이름을 알기 쉽게 `Prompt Data` 정도로 변경해 주세요.

## 2단계: 폴더 ID 복사하기
코드에 "이 이미지를 어느 폴더에 저장할지" 알려줘야 합니다.
1. 웹 브라우저에서 `image prompt data` 폴더를 열고 주소창을 봅니다.
2. 주소가 `https://drive.google.com/drive/folders/1aBcD2eFgH3iJkL...` 와 같이 보일 것입니다.
3. 여기서 `folders/` 뒤에 있는 **알파벳과 숫자가 섞인 긴 문자열**이 바로 폴더 ID입니다. 이 값을 복사해 둡니다.

## 3단계: 구글 Apps Script 코드 붙여넣기
1. 방금 만든 **생성한 스프레드시트 화면**에서 상단 메뉴의 **[확장 프로그램]** -> **[Apps Script]**를 클릭합니다.
2. 새 창이 열리면 원래 있던 코드를 모두 지우고, 아래의 코드를 복사해서 붙여넣습니다.

```javascript
// ====== 이 아래 줄의 따옴표 안에 아까 복사한 폴더 ID를 붙여넣으세요! ======
const FOLDER_ID = "여기에_폴더_ID를_붙여넣으세요"; 
// ===============================================================

function doPost(e) {
  try {
    const data = e.parameter;
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    if (data.action === "upload") {
      const folder = DriveApp.getFolderById(FOLDER_ID);
      const base64Data = data.base64.split(",")[1];
      const blob = Utilities.newBlob(Utilities.base64Decode(base64Data), data.mimeType, data.filename);
      const file = folder.createFile(blob);
      
      const fileUrl = file.getUrl();
      const fileId = file.getId();
      file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      
      const now = new Date();
      const formattedDate = Utilities.formatDate(now, Session.getScriptTimeZone(), "yyyy. MM. dd. HH:mm:ss");
      // 컬럼 순서: Date | Category | Prompt | Image URL | File ID | Title | AI Thinking | Analysis | Status
      sheet.appendRow([
        formattedDate,
        data.category,
        data.prompt,
        fileUrl,
        fileId,
        data.title || "",
        data.thinking || "",
        data.analysis || "",
        data.status || "success"
      ]);
      
      return ContentService.createTextOutput(JSON.stringify({success: true, fileUrl: fileUrl})).setMimeType(ContentService.MimeType.JSON);
    }
    
    if (data.action === "edit") {
      const values = sheet.getDataRange().getValues();
      for (let i = 1; i < values.length; i++) {
        if (values[i][4] === data.fileId) {
          sheet.getRange(i + 1, 2).setValue(data.category);
          sheet.getRange(i + 1, 3).setValue(data.prompt);
          sheet.getRange(i + 1, 6).setValue(data.title);
          sheet.getRange(i + 1, 7).setValue(data.thinking || "");
          sheet.getRange(i + 1, 8).setValue(data.analysis || "");
          sheet.getRange(i + 1, 9).setValue(data.status || "success");
          return ContentService.createTextOutput(JSON.stringify({success: true})).setMimeType(ContentService.MimeType.JSON);
        }
      }
      return ContentService.createTextOutput(JSON.stringify({success: false, error: "Post not found."})).setMimeType(ContentService.MimeType.JSON);
    }
    
    if (data.action === "delete") {
      const values = sheet.getDataRange().getValues();
      for (let i = 1; i < values.length; i++) {
        if (values[i][4] === data.fileId) {
          sheet.deleteRow(i + 1);
          try { DriveApp.getFileById(data.fileId).setTrashed(true); } catch(err) {}
          return ContentService.createTextOutput(JSON.stringify({success: true})).setMimeType(ContentService.MimeType.JSON);
        }
      }
      return ContentService.createTextOutput(JSON.stringify({success: false, error: "Post not found."})).setMimeType(ContentService.MimeType.JSON);
    }
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({success: false, error: err.toString()})).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const results = [];
  const startIndex = Math.max(1, (data.length > 0 && data[0][0] === "Date") ? 1 : 0);
  
  for (let i = startIndex; i < data.length; i++) {
    if(!data[i][4]) continue; 
    results.push({
      date: data[i][0],
      category: data[i][1],
      prompt: data[i][2],
      url: "https://drive.google.com/uc?id=" + data[i][4],
      originalUrl: data[i][3],
      title: data[i][5] || "",
      id: data[i][4],
      thinking: data[i][6] || "",   // AI 사고과정
      analysis: data[i][7] || "",   // 분석 메모
      status: data[i][8] || "success" // 성공/실패 여부
    });
  }
  
  results.reverse();
  return ContentService.createTextOutput(JSON.stringify(results)).setMimeType(ContentService.MimeType.JSON);
}

function setup() {
  // 최초 한 번 실행: 시트 맨 위 첫 줄에 이름(헤더)을 달아줍니다.
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(["Date", "Category", "Prompt", "Image URL", "File ID", "Title", "AI Thinking", "Analysis", "Status"]);
  }
}
```



3. 위 코드의 세 번째 줄 `"여기에_폴더_ID를_붙여넣으세요"` 부분을 지우고 조금 전 복사한 **내 폴더 ID**를 붙여넣습니다. (따옴표는 유지)
4. 저장 아이콘(💾 스크립트 저장)을 누릅니다.

## 4단계: 권한 허용 및 배포 (중요!)
이 코드가 외부에 갤러리 앱과 통신할 수 있게 API(Web App)로 배포합니다.

1. 화면 위쪽의 툴바 가운데 쯤 콤보박스(아마 기본적으로 `doPost`로 되어 있을 것)를 눌러서 **`setup`**을 선택하고 **[▶ 실행]** 버튼을 누릅니다.
2. `[권한 검토]` 창이 뜨면 클릭하고 자신의 구글 계정을 선택합니다.
3. `[안전하지 않음으로 돌아가기]`(또는 하단의 고급 탭)를 눌러 권한을 허용해줍니다.
   - *(이 과정은 자기 자신의 계정 권한을 구글 시트에게 승인하는 것이라 100% 안전합니다)*
4. 다시 상단 우측 파란색 **[배포(Deploy)] -> [새 배포]**를 클릭합니다.
5. 톱니바퀴(유형 선택) 아이콘을 눌러서 **[웹 앱(Web App)]**을 선택합니다.
6. 중요한 설정 두 가지를 변경합니다:
   - **실행하는 사용자(Execute as)**: `나(Me)` 선택
   - **액세스할 수 있는 사용자(Who has access)**: **`모든 사용자(Anyone)`** 선택 (이걸 선택해야 로컬 HTML 파일에서 접근 가능합니다)
7. **[배포]**를 누르면 잠시 후 나오는 **`웹 앱 URL (Web app URL)`** (`https://script.google.com/macros/s/.../exec`)을 복사합니다.

### 🎉 끝입니다!
복사하신 이 **`웹 앱 URL`**을 저에게 채팅창에 남겨주시면, 제가 바로 연동된 예쁜 HTML / CSS / JS 갤러리 껍데기 파일을 만들어 드리겠습니다!
