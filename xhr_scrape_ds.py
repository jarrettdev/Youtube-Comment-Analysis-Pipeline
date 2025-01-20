#xhr_scrape_ds.py
'''
script that intercepts the xhr requests from the youtube api,
performs some data wrangling, and saves the data to a file
'''
import json
import os
import subprocess
from urllib.parse import urlparse
from datetime import datetime
from process_output import process_file
import pandas as pd
import json
from datetime import datetime
import traceback
#getenv
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz



#TODO: add a way to get the videoId from the xhr request

load_dotenv()


def parse_published_time(published_time):
    current_time = datetime.now()
    time_parts = published_time.split()
    number = int(time_parts[0])
    unit = time_parts[1]

    if 'minute' in unit:
        return current_time - timedelta(minutes=number)
    elif 'hour' in unit:
        return current_time - timedelta(hours=number)
    elif 'day' in unit:
        return current_time - timedelta(days=number)
    elif 'month' in unit:
        return current_time - relativedelta(months=number)
    elif 'year' in unit:
        return current_time - relativedelta(years=number)
    else:
        return current_time  # Default to current time if something unexpected occurs


def get_substring_after_tld(url):
    parsed_url = urlparse(url)
    tld_index = parsed_url.netloc.rfind('.') # Find the last dot in the netloc part
    if tld_index != -1:
        return parsed_url.netloc[tld_index+1:] + parsed_url.path
    return '' # Return empty string if TLD is not found



def sanitize_substring(substring):
    return substring.replace(':', '_').replace('/', '_').replace('.','_').replace('www', '_').replace('https', '_').replace('http', '_').replace('?','_')


with open('config.json', 'r') as f:
    config = json.load(f)

# the xhr url is read in from config.json
# this is to handle the case where the api makes a change to the url
target_urls = config['xhr_urls']

target_strs = [target_str for target_str in target_urls]

target_str = target_strs[0]
substring_after_tld = get_substring_after_tld(target_str)
target_dir_str = sanitize_substring(substring_after_tld)
out_dir = f'output/{target_dir_str}'
if not os.path.exists(out_dir):
    os.makedirs(out_dir)


# Global variable to store the last tracked URL
last_url = None
video_id = None



def extract_comment_info(comment_entity_payload):
    try:
        # Extracting properties
        properties = comment_entity_payload['properties']
        author = comment_entity_payload['author']
        toolbar = comment_entity_payload['toolbar']
        print(f'=====================================\nToolbar: {toolbar}\n=====================================\n')
        like_count = toolbar['likeCountNotliked']
        reply_count = toolbar['replyCount']

        # Extracting individual fields
        content = properties['content']['content']
        comment_id = properties['commentId']
        published_time = properties['publishedTime']
        
        reply_level = properties['replyLevel']

        # Extracting author details
        channel_id = author['channelId']
        display_name = author['displayName']
        avatar_url = author['avatarThumbnailUrl']
        is_verified = author['isVerified']
        #REASSIGNMENT!
        author = properties['authorButtonA11y']

        # Print extracted information
        print(f"Comment ID: {comment_id}")
        print(f"Content: {content}")
        print(f"Published Time: {published_time}")
        print(f"Reply Level: {reply_level}")
        print(f"Channel ID: {channel_id}")
        print(f"Display Name: {display_name}")
        print(f"Avatar URL: {avatar_url}")
        print(f"Verified: {'Yes' if is_verified else 'No'}")
        
        json_obj = {
            "comment_id": comment_id,
            "0": content,
            "like_count": like_count,
            "reply_count": reply_count,
            "author": author,
            "published_time": published_time,
            "reply_level": reply_level,
            "channel_id": channel_id,
            "display_name": display_name,
            "avatar_url": avatar_url,
            "verified": is_verified
        }
        return json_obj

    except Exception as e:
        print(f"Error extracting information: {e}")
        traceback.print_exc()

def response(flow):
    global last_url  # Declare last_url as global so we can modify it
    #global video_id
    flow_url = flow.request.url

    if target_str in flow_url.lower():
        # print(f'XHR URL: {flow_url}\n\n\n\n\n\n')
        # Parse the JSON response from the XHR request
        # print(flow_url)
        try:
            response_dict = json.loads(flow.response.text)
        except Exception:
            response_dict = {
                'content': flow.response.text
            }

        # Append the last tracked URL to the response_dict
        if last_url is not None:
            response_dict['tracked_url'] = last_url
        # print(response_dict)

        # Save the metadata and XHR response to a file
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        response_dict['timeOfScrape'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            response_dict['videoId'] = str(response_dict).split("watch%253Fv%253D")[1].split('&')[0]
            response_dict['video_id'] = 'aaa'
        except:
            response_dict['videoId'] = 'N/A'
            pass
        with open(f'{out_dir}/data.json', 'a') as f:
            json.dump(response_dict, f)
            f.write(',\n')
        youtube_comments_object = process_file('com_youtubei_v1_next/data.json')
        comments_data = []
            
        # Iterate through the youtube_comments_object
        for i, comment_object in enumerate(youtube_comments_object):
            framework_updates = None
            try:
                framework_updates = comment_object['frameworkUpdates']
            except Exception as e:
                # try legacy comments
                print(f'Error extracting frameworkUpdates for comment {i}: {e}')
                continue
            #print(framework_updates)
            mutations = framework_updates['entityBatchUpdate']['mutations']
            for mutation in mutations:
                #print(mutation.keys())
                if ('payload' not in mutation.keys()):
                    continue
                #try to get commentEntityPayload
                comment_entity_payload = None
                comment_obj = None
                try:
                    comment_entity_payload = mutation['payload']['commentEntityPayload']
                    print('commentEntityPayload')
                    comment_obj = extract_comment_info(comment_entity_payload)
                except Exception as e:
                    print(f'Error extracting commentEntityPayload for comment {i}: {e}')
                    traceback.print_exc()
                    #print(mutation['payload'].keys())
                    continue
                comments_data.append(comment_obj)
            #by this point, we have a comment!
            continue


        # Convert to a DataFrame
        df_comments = pd.DataFrame(comments_data)
        #video_id = youtube_comments_object[0]['videoId']
        #make video_id the first item in data.json ['videoId']
        video_id = youtube_comments_object[0]['videoId']
        df_comments['video_id'] = video_id
        print(df_comments)
        df_comments['Date'] = df_comments['published_time'].apply(parse_published_time)
        # # Localize the datetime to UTC
        df_comments['Date'] = df_comments['Date'].dt.tz_localize('UTC')

        # # Convert UTC to Arizona Time (MST, which is UTC-7)
        arizona_tz = pytz.timezone('America/Phoenix')
        df_comments['Date'] = df_comments['Date'].dt.tz_convert(arizona_tz)

        # # Extract datetime components
        df_comments['Day_of_Week'] = df_comments['Date'].dt.day_name()
        df_comments['Hour_of_Day'] = df_comments['Date'].dt.hour
        #replace double quotes
        df_comments['0'] = df_comments['0'].str.replace('"', "'")
        if not os.path.exists('transcript_scrape/scraped_comments'):
            os.makedirs('transcript_scrape/scraped_comments')
        df_comments.to_csv(f'/root/snap/misc/general_scrape/scrape/transcript_scrape/scraped_comments/{video_id}_comments.csv', index=False)
        print(f'Saved comments for {video_id} to transcript_scrape/scraped_comments/{video_id}_comments.csv')
