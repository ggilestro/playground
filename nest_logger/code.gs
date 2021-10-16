/**
 * download the latest thermostat data
 */
async function getThermostat() {
  let data = new Object();
  try {
    // setup the SMD API URL, headers, and params
    //getService().refresh();
    var token = getService().getAccessToken();
    //console.log(token);

    const url = 'https://smartdevicemanagement.googleapis.com/v1';
    const endpoint = '/enterprises/' + PROJECT_ID + '/devices';
    const headers = {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    }
    const params = {
      'headers': headers,
      'method': 'get',
      'muteHttpExceptions': true
    }
    // url fetch to call api
    const response = UrlFetchApp.fetch(url + endpoint, params);
    const nestData = JSON.parse(response.getContentText());
    
    // I have only one Nest device so I don't need to hunt for it
    const thermostatData = nestData['devices'][0]['traits'];

    data['info'] = thermostatData["sdm.devices.traits.Info"]
    data['humidity'] = thermostatData["sdm.devices.traits.Humidity"];
    data['connectivity'] = thermostatData["sdm.devices.traits.Connectivity"];
    data['fan'] = thermostatData["sdm.devices.traits.Fan"];
    data['thermostatMode'] = thermostatData["sdm.devices.traits.ThermostatMode"];
    data['thermostatEco'] = thermostatData["sdm.devices.traits.ThermostatEco"];
    data['thermostatHvac'] = thermostatData["sdm.devices.traits.ThermostatHvac"];
    data['thermostatTemperatureSetpoint'] = thermostatData["sdm.devices.traits.ThermostatTemperatureSetpoint"];
    data['temperature'] = thermostatData["sdm.devices.traits.Temperature"];

  }
  catch (e) {
    Logger.log('Error: ' + e);
  }
  return data;
}

/**
 * collect the data we care about to record on our spreadsheet
 */
async function measure() {

  let thermostat_promise = getThermostat();
  let weather_promise = retrieveWeather(WEATHER_STATION);
  const async_data = await Promise.all([thermostat_promise, weather_promise])
  const thermostat = async_data[0]
  const weather = async_data[1]

  // setpoints depend on mode
  let cooling_setpoint = 0;
  let heating_setpoint = 0;
  let eco_off = (thermostat['thermostatEco']['mode'] === 'OFF');
  if ( thermostat['thermostatMode']['mode'] === 'COOL' || thermostat['thermostatMode']['mode'] === 'HEATCOOL') {
    cooling_setpoint = eco_off ? thermostat['thermostatTemperatureSetpoint']['coolCelsius'] : thermostat['thermostatEco']['coolCelsius'];
  }
  if ( thermostat['thermostatMode']['mode'] === 'HEAT' || thermostat['thermostatMode']['mode'] === 'HEATCOOL') {
    heating_setpoint = eco_off ? thermostat['thermostatTemperatureSetpoint']['heatCelsius'] : thermostat['thermostatEco']['heatCelsius'];
  }

  var time = new Date();
  var timeZone = "Europe/London";
  var timeStamp = Utilities.formatDate(new Date(), timeZone, "yyyy/MM/dd HH:mm:ss");

  let data = [];
  data.push(
    timeStamp,
    Utilities.formatDate(time, Session.getScriptTimeZone(), "YYYY"),
    Utilities.formatDate(time, Session.getScriptTimeZone(), "MM"),
    Utilities.formatDate(time, Session.getScriptTimeZone(), "dd"),
    thermostat['temperature']['ambientTemperatureCelsius'],
    thermostat['humidity']['ambientHumidityPercent'],
    weather['outside_tempC'],
    weather['outside_humidity'],
    weather['outside_pressure'],
    ((thermostat['thermostatHvac']['status'] === 'COOLING') ? 73 : ((thermostat['thermostatHvac']['status'] === 'HEATING') ? 72 : 0)),
    weather['description'],
    thermostat['thermostatHvac']['status'],
    thermostat['connectivity']['status'],
    thermostat['thermostatMode']['mode'],
    thermostat['thermostatEco']['mode'],
    cooling_setpoint,
    heating_setpoint
    );

  console.log('measurement: ' + JSON.stringify(data));
  return data;
}

/**
 * grab all data and write a new row to our spreadsheet
 */
async function logMeasurement() {
  try {
    let startDate = new Date();
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName('Data');

     // add header if needed
    if ( sheet.getLastRow() == 0 ) {
      headers = [
        'Date/Time',
        'Month',
        'Day',
        'Year',
        'Inside Temperature',
        'Inside Humidity',
        'Outside Temperature',
        'Outside Humidity',
        'Heat_Usage',
        'AC_Usage',
        'Weather',
        'AutoAway'
      ];
      sheet.getRange(sheet.getLastRow()+1, 1, 1, headers.length).setValues([headers]);
    }

    data = await measure();
    sheet.getRange(sheet.getLastRow()+1, 1, 1, data.length).setValues([data]);
    let endDate = new Date();
    let duration_msec = endDate.getTime() - startDate.getTime();
    Logger.log('success! runtime in milliseconds was: ' + duration_msec);
  }
  catch(e) {
    Logger.log('Error: ' + e);
  }
}

/**
 * function to retrieve latest weather forecast for nearby area
 * list of stations:
 * https://forecast.weather.gov/stations.php
 */
function retrieveWeather(stationCode) {
  //get outside data
  const weatherArray = {};

  try {
    const weatherUrl = 'http://api.openweathermap.org/data/2.5/weather?id=' + stationCode + '&appid=' + WEATHER_TOKEN;
    const response = UrlFetchApp.fetch(weatherUrl);
    const weatherData = JSON.parse(response.getContentText());

    // parse the data which are something like the below
    // {"coord":{"lon":-0.2833,"lat":51.3667},"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04d"}],"base":"stations","main":{"temp":285.66,"feels_like":285.5,"temp_min":284.33,"temp_max":287.71,"pressure":1029,"humidity":97},"visibility":8000,"wind":{"speed":1.54,"deg":290},"clouds":{"all":90},"dt":1633856394,"sys":{"type":2,"id":19889,"country":"GB","sunrise":1633846586,"sunset":1633886368},"timezone":3600,"id":3333160,"name":"Kingston upon Thames","cod":200}

    weatherArray['outside_tempC'] = convertKtoC(weatherData["main"]["temp"]);
    weatherArray['outside_humidity'] = (weatherData["main"]["humidity"]);
    weatherArray['outside_pressure'] = (weatherData["main"]["pressure"]);
    weatherArray['description'] = (weatherData["weather"][0]["main"]);
    weatherArray['windDirection'] = weatherData['wind']['deg'];;
    weatherArray['windSpeed'] = weatherData['wind']['speed'];
    weatherArray['visibility'] = weatherData['visibility'];
    weatherArray['time'] = new Date();
  }

  catch (e) {
    Logger.log('Error: ' + e);
  }
  
  return weatherArray;

}
