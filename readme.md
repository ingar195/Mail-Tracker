# Mail Tracker
This is a simple program to collect all your tracking needs into one place 
## Supported providers:
- Posten.no
- PostNord.no
## How to start:
- Install Python dependencies:
``` bash
pip install -r requirements.txt
```
- run the server:
```bash 
python3 tracker.py
```
## How to use:
- Write a name and a tracking ID in their fields
- Provider dropdown, there you have these options:  
    - Posten
    - PostNord
- Add: will add it to the list, and the state will be updated each add and refresh of the site 
- You can delete the list entry with the delete button

- This will start the server [here](http://127.0.0.1:1234) 


## Pushbullet
To generate a API key use this [link](https://www.pushbullet.com/#settings/account)

## Plans:
- Alert's
    - Slack
    - Pushbullet
    - Discord
- Create a docker image 
- Auto reload when new data is available 
