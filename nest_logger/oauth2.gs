var AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth';
var TOKEN_URL = 'https://www.googleapis.com/oauth2/v4/token';
// Use an array for multiple scopes ['https://www.googleapis.com/auth/drive']
var SCOPE = 'https://www.googleapis.com/auth/sdm.service';
var REDIRECT_URI = 'https://script.google.com/macros/d/' + ScriptApp.getScriptId() + '/usercallback';

// After execution 1 of Main, enter the OAuth code inside the quotes below:
var CODE = '';


/**
 * Logs the redirect URI set up for the client
 *  -- run this function to manually grant permissions
 */
function logRedirectUri() {
  var service = getService();
  service.reset();
  if (service.hasAccess()) {
      // get the access token
      const access_token = service.getAccessToken();
  } else {
    var authorizationUrl = service.getAuthorizationUrl();
    Logger.log('Open the following URL and re-run the script: %s', authorizationUrl);
  }
}

/**
 * Create the OAuth2 service helper
 */
function getService() {
  // Create a new service with the given name. The name will be used when
  // persisting the authorized token, so ensure it is unique within the
  // scope of the property store.
  return OAuth2.createService('smd')
      // Set the endpoint URLs.
      .setAuthorizationBaseUrl(AUTH_URL)
      .setTokenUrl(TOKEN_URL)

      // Set the client ID and secret.
      .setClientId(OAUTH_CLIENT_ID)
      .setClientSecret(OAUTH_CLIENT_SECRET)

      // Set the name of the callback function that should be invoked to
      // complete the OAuth flow.
      .setCallbackFunction('authCallback')

      // Set the property store where authorized tokens should be persisted.
      .setPropertyStore(PropertiesService.getUserProperties())

      // Set the scope and additional Google-specific parameters.
      .setScope(SCOPE)
      .setParam('access_type', 'offline')

      // Important! Consent prompt is required to ensure a refresh token is always
      // returned when requesting offline access.
      .setParam('prompt', 'consent')
      .setParam('login_hint', Session.getActiveUser().getEmail());
}


/**
 * Report success or failure of permissions
 */
function authCallback(request) {
  const service = getService();
  const isAuthorized = service.handleCallback(request);
  if (isAuthorized) {
    return HtmlService.createHtmlOutput('Success! You can close this tab.');
  } else {
    return HtmlService.createHtmlOutput('Denied. You can close this tab');
  }
}
