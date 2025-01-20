'''
script that performs analysis (keyword, sentiment, engagement, top comments) on videos
and throws the results into MongoDB
'''

#%%
import pandas as pd
import os
from glob import glob
import matplotlib.pyplot as plt
import json
from comment_analysis import CommentAnalyzer
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
# TODO: generalize
# database of current domain or niche
db = client['yt_comments']

channel_to_state = pd.read_csv('master_channel_to_states.csv')

videos = pd.read_csv('data/master_videos.csv')

def load_comments(video_id, channel_id):
    file_path = f'data/{channel_id}/{video_id}/comments.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df['video_id'] = video_id
        return df
    return None

all_comments = []
for _, row in videos.iterrows():
    comments = load_comments(row['video_id'], row['channel_id'])
    if comments is not None:
        all_comments.append(comments)
print(len(all_comments))
print('Comments loaded')

comments = pd.concat(all_comments, ignore_index=True)
#%%
videos_with_state = pd.merge(videos, channel_to_state, on='channel_id', how='left')
comments_with_video = pd.merge(comments, videos_with_state[['video_id', 'state', 'video_title','video_url','views']], on='video_id', how='left')
#%%
#we need to convert like_count to int and handle periods, commas, and other non-numeric characters (k, M)
def convert_to_int(value):
    if pd.isna(value):
        return None
    if str(value).strip() == '':
        return None
    value = str(value)
    value = value.replace(',', '').replace('.', '').replace('k', '000').replace('M', '000000')
    return int(value)

comments_with_video['like_count'] = comments_with_video['like_count'].apply(convert_to_int)
#%%
top_comments_by_state = comments_with_video.sort_values('like_count', ascending=False).groupby('state').first()

print(top_comments_by_state[['0', 'like_count']])

avg_likes_by_state = comments_with_video.groupby('state')['like_count'].mean().sort_values(ascending=False)

print("\nAverage likes per comment by state:")
print(avg_likes_by_state)

comment_count_by_state = comments_with_video['state'].value_counts()

print("\nComment count by state:")
print(comment_count_by_state)
# %%
#most liked comment in each state
most_liked_comment_by_state = comments_with_video.sort_values('like_count', ascending=False).groupby('state').first()
print(most_liked_comment_by_state[['0', 'like_count']])
# %%
comments_with_video.to_csv('data/comments_with_video.csv', index=False)

for _, row in comments_with_video.iterrows():
    comment_data = row.to_dict()
    
    db.comments_with_video.update_one(
        {'comment_id': comment_data['comment_id']},
        {'$set': comment_data},
        upsert=True
    )

# TODO: generalize
analyzer = CommentAnalyzer(comments_with_video)

keyword_analysis = analyzer.analyze_keywords_by_state()
sentiment_analysis = pd.DataFrame(list(analyzer.get_sentiment_by_state()))
engagement_metrics = analyzer.get_engagement_metrics()
top_comments_by_state = analyzer.get_top_comments_by_state()
top_comments_by_video = analyzer.get_top_comments_by_video()

state_summary = {}
for state in comments_with_video['state'].unique():
    if pd.isna(state):
        continue
        
    state_summary[state] = {
        'keywords': keyword_analysis.get(state, {}),
        'sentiment': sentiment_analysis[sentiment_analysis['state'] == state].to_dict('records')[0],
        'engagement': engagement_metrics.loc[state].to_dict(),
        'top_comments': [comment for comment in top_comments_by_state if comment['state'] == state]
    }

video_summary = {}
for video_id in comments_with_video['video_id'].unique():
    video_summary[video_id] = {
        'top_comments': [comment for comment in top_comments_by_video if comment['video_id'] == video_id]
    }

db.state_analysis.delete_many({})
db.state_analysis.insert_many([{'state': k, **v} for k, v in state_summary.items()])

db.video_analysis.delete_many({})
db.video_analysis.insert_many([{'video_id': k, **v} for k, v in video_summary.items()])

# %%

# visualize top comments by state
for state in comments_with_video['state'].unique():
    top_comments = [comment for comment in top_comments_by_state if comment['state'] == state]
    print(f"Top comments for {state}:")
    for comment in top_comments:
        print(f" - {comment['0']} (Likes: {comment['like_count']})")
    #print current time in human readable format
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
# %%
