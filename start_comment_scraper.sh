#!/bin/bash
# start_comment_scraper.sh

# Command to start the first screen session and run the mitmdump command. Intercepts traffic and runs the script xhr_scrape_ds.py
screen -dmS comment_interceptor bash -c 'cd /root/snap/misc/general_scrape/scrape; mitmdump -s xhr_scrape_ds.py'

# start the stream that processes new videos
screen -dmS video_stream bash -c 'cd /root/snap/misc/general_scrape/scrape; python3 process_stream.py'

# run index.js (this whole system) from a crontab
#*/375 * * * * cd /root/snap/misc/general_scrape/scrape &&  xvfb-run -a /root/.nvm/versions/node/v21.6.2/bin/node index.js && /usr/bin/python3 analysis.py >> output.log 2>&1