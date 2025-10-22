/**
 * Ski Course Registration - Cloud Function Trigger
 * Automatically triggers on Google Form submissions
 */

const CLOUD_FUNCTION_URL = "https://us-central1-kursanmeldungen-439011.cloudfunctions.net/RegrstrationServiceFunction";
const PROPERTIES = PropertiesService.getScriptProperties();
const LAST_REQUEST_KEY = "lastRequestTime";
const MIN_INTERVAL_MS = 60000; // 60 seconds

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Kursanmeldung')
    .addItem('Synchronisieren', 'callCloudFunction')
    .addItem('Setup Trigger', 'setupTrigger')
    .addToUi();
}

/**
 * Automatically called when form is submitted
 * Setup: Run setupTrigger() once to install
 */
function onFormSubmit(e) {
  Logger.log("Form submitted, triggering cloud function");
  callCloudFunction();
}

/**
 * Install form submission trigger (run once)
 */
function setupTrigger() {
  // Remove existing triggers to avoid duplicates
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'onFormSubmit') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // Create new trigger
  ScriptApp.newTrigger('onFormSubmit')
    .forSpreadsheet(SpreadsheetApp.getActive())
    .onFormSubmit()
    .create();
  
  SpreadsheetApp.getUi().alert("Trigger installiert! Cloud Function wird bei jeder Anmeldung ausgeführt.");
}

function callCloudFunction() {
  // Rate limit check
  const lastRequest = PROPERTIES.getProperty(LAST_REQUEST_KEY);
  if (lastRequest && (new Date().getTime() - parseInt(lastRequest)) < MIN_INTERVAL_MS) {
    Logger.log("Rate limited, skipping request");
    return;
  }
  
  const options = {
    'method': 'get',
    'headers': {"Authorization": "Bearer " + ScriptApp.getOAuthToken()},
    'muteHttpExceptions': true
  };
  
  try {
    const response = UrlFetchApp.fetch(CLOUD_FUNCTION_URL, options);
    const code = response.getResponseCode();
    const text = response.getContentText();
    
    Logger.log(`Response ${code}: ${text}`);
    
    if (code === 200) {
      PROPERTIES.setProperty(LAST_REQUEST_KEY, new Date().getTime().toString());
    } else {
      Logger.log(`Error ${code}: ${text}`);
    }
  } catch (error) {
    Logger.log("Error: " + error);
  }
}