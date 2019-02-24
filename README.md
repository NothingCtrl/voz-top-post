VOZ TOP POST
============
Simple app to filter useful / hot topics in forum [VOZ forum](http://forums.voz.vn), after filter, save thread(s) to sub-folder voz/

Requirement:
---
* Install Python 3
* Create virtualenv and install required packages in `requirements.txt` using pip
* Add your browser session value to file `cookie.json`, example file `cookie.json` content:
    ```json
    {
      "cookie": "vfsessionhash=your_session_hash_of_voz_forum"
    }
    ```
    * Note: To get forum session hash, you can using browser extension (_EditThisCookie_) or in Chrome, press F12 and find it in GET request header value 
* Run app: `python app.py`