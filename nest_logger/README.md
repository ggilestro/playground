The Google NEST data are accessible through the Device Access Program from Google. This requires developer access (for a $5 one-off fee) and a little bit of technical knowledge. This project will guide you towards a google spreadsheet that logs NEST data and weather data. 

1. [Register for the Device Access Program](https://developers.google.com/nest/device-access/registration), which incurs a non-refundable $5 fee.
2. Login to your [Google Console Dashboard](https://console.cloud.google.com/home/dashboard) and create a new project. Call the project with a recognisible name, like "Google NEST logger".
3. [Enable the Google API management](https://console.cloud.google.com/apis/library/smartdevicemanagement.googleapis.com?project=gothic-standard-168517) for this project. If you have multiple projects already, make sure it is this one you are enabling the API for. Check the project name next to the header. 
    
    ![image](https://user-images.githubusercontent.com/696901/137586206-5a45502e-e8f2-4da8-9456-a7bb77be439f.png)
    
4. From the Google Cloud Console, select APIs and services / Credentials and create new credentials. Call the new credentials something clear like `Google Nest Logger Macro`. Take note of the two values: `Client ID` and `Client secret`. 
    
    ![image](https://user-images.githubusercontent.com/696901/137586212-c03485fb-e56a-42a8-996c-f503d8a8695f.png)
    
5. Select the tab called `OAuth consent screen`, give consent then publish the consent screen (should not be in test status but in publishing status).
6. Create a new Google Sheet (pro tip: type sheet.new into your browser!). Give it an appropriate name of your choice. This is where your data will be saved.
7. In your newly created sheet, click on the Tools / Script editor in the toolbar and upload the four google scripts files of this repository.
8. In your script editor, select the file called `helperFunctions.gs`and run the function called `giveMeRedirectURI`. This will return a URL in your console. Copy that URL and paste it in the appropriate credential section of your google console (the one you created at step 4).
    
    ![image](https://user-images.githubusercontent.com/696901/137586235-fc3a8238-6353-4582-8c6a-3997adf444f5.png)
    
    ![image](https://user-images.githubusercontent.com/696901/137586246-fa2c294f-fc6e-4392-88a4-b8835e1933fb.png)
    
9. Back to your Device Access Console, create a new project
10. When prompted, add the OAuth client ID from your Google Cloud project to this new Smart Device project. You took note of this at step 4.
    
    ![image](https://user-images.githubusercontent.com/696901/137586264-c84feaa0-a0d3-4599-8182-dac5c8c0567a.png)
    
11. Activate your Nest device(s) when prompted during project creation.
12. Take note of your `Project_ID` 
    
    ![image](https://user-images.githubusercontent.com/696901/137586284-4d363fd5-d28b-4074-a716-d35b1a7ce108.png)
    
13. Go back to your script editor (same as point 7) and add the `oauth2`library following the directions below:
    1. Click on the menu item "Resources > Libraries..."
    2. In the "Find a Library" text box, enter the script ID `1B7FSrk5Zi6L1rSxxTDgDEUsPzlukDsi4KGuTMorsTQHhGBzBkMun4iDF`and click the "Select" button.
    3. Choose a version in the dropdown box (usually best to pick the latest version).
    4. Click the "Save" button.
14. Create an Openweather app it token following instructions [https://openweathermap.org/appid](https://openweathermap.org/appid). Take note of your Key from your openweather console.
    
    ![image](https://user-images.githubusercontent.com/696901/137586310-0f82041c-49e4-47f6-bab5-b547b1fb7253.png)
    
15.  Find the openweather station code for your city. Look for your city on the openweather site and take note of the city ID in the URL. For instance, the city ID for London, GB is 2643743.
    
    ![image](https://user-images.githubusercontent.com/696901/137586319-aeed77ef-a874-4e35-a847-cb761bb2743e.png)
    
16. Go back to your script editor and select the file called `globalVariables.gs`. Now you have all the values you need to enter. The only value you have not collected yet is the serial number of your thermostat. You can find that value on the thermostat itself, in the settings page of the thermostat, or on the nest app on your phone. See [here](https://support.google.com/googlenest/thread/15621991/where-do-i-find-the-model-for-my-nest-thermostat?hl=en) if you need help. 
    
    ```jsx
    /**
     * Global Variables
     */
    const PROJECT_ID = 'THE PROJECT ID FROM STEP 12';
    const OAUTH_CLIENT_ID = 'THE CLIENT ID FROM STEP 4';
    const OAUTH_CLIENT_SECRET = 'THE CLIENT SECRET FROM STEP 4';
    const DEVICE_ID = 'THESERIALNUMBEROFYOURDEVICE';
    
    // create your openweatherAPI token following instructions here. https://openweathermap.org/appid
    const WEATHER_TOKEN = 'YOUR API CODE FROM STEP 14';
    // to find city ID go to "http://openweathermap.org/find?q=" search for your city, click on the city link and the ID will be the 7 digit number in the URL 
    const WEATHER_STATION = YOURSTATIONCODEFROMSTEP15;
    ```
    
17. Now from the editor select the file called `[oauth2.gs](http://oauth2.gs)` and run the function `logRedirectUri`. This will output a URL. Open that URL in another browser tab and authorise everything you need to authorise.
18. Finally, open the file called `code.gs`and run the function called `logMeasurement`. If everything is setup properly you should see the first line of data logged in the spreadsheet you created at step. 
19. If step 19 was successful, all you need to add is a time trigger. Click on trigger, then find the "+ Add trigger" button on the bottom right corner and add a timed trigger. 
    
    ![image](https://user-images.githubusercontent.com/696901/137586340-916a9869-aeb3-43f1-b608-2f71eef3634c.png)
    
    ![image](https://user-images.githubusercontent.com/696901/137586350-2567639b-b79f-420f-b777-9f8378e73d9f.png)
    
20. I run mine every 15 minutes.
