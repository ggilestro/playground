/**
 * function to convert celcius to farenheit
 */
const convertCtoF = t => ( (t * 9/5) + 32 );
const convertFtoC = t => ( (t - 32) * 5/9 );
const convertKtoC = t => (  t - 273.15 );

/**
 * Run this once to know what your REDIRECT URL should be. Add this value to the auth section in your google console project
 */
function giveMeRedirectURI () {
  console.log ('https://script.google.com/macros/d/' + ScriptApp.getScriptId() + '/usercallback');
}
