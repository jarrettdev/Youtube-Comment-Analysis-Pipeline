import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json


load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['yt_comments']

class CommentAnalyzer:
    def __init__(self, comments_df):
        self.df = comments_df
        self.keyword_groups = {
            'incident_type': {
                'accidents': ['crash', 'collision', 'accident', 'hit', 'wreck'],
                'congestion': ['backup', 'gridlock', 'jam', 'standstill', 'slow'],
                'construction': ['roadwork', 'construction', 'repairs', 'detour', 'closure'],
            },
            'location_type': {
                'highways': ['interstate', 'highway', 'freeway', 'i-', 'exit'],
                'local_roads': ['street', 'intersection', 'boulevard', 'avenue', 'road'],
                'infrastructure': ['bridge', 'tunnel', 'ramp', 'lane', 'merge'],
            },
            'impact': {
                'timing': ['delay', 'late', 'minutes', 'hours', 'commute'],
                'severity': ['fatal', 'serious', 'blocked', 'closed', 'emergency'],
                'weather': ['ice', 'snow', 'rain', 'fog', 'conditions'],
            },
            'solutions': {
                'alternate_routes': ['detour', 'alternate', 'route', 'bypass', 'shortcut'],
                'suggestions': ['fix', 'widen', 'improve', 'maintain', 'upgrade'],
                'services': ['tow', 'police', 'ambulance', 'crew', 'response']
            }
        }

    def analyze_keywords_by_state(self):
        """Analyze keyword frequencies by state with normalization"""
        results = defaultdict(lambda: defaultdict(dict))
        
        state_comment_counts = self.df['state'].value_counts()
        
        for group_name, keyword_group in self.keyword_groups.items():
            for topic, keywords in keyword_group.items():
                print(f"Analyzing {topic} for {group_name}")
                pattern = '|'.join(keywords)
                
                mentions = self.df[self.df['0'].str.contains(pattern, case=False, na=False)]
                mentions_by_state = mentions['state'].value_counts()
                
                normalized_mentions = (mentions_by_state / state_comment_counts * 100).round(2)
                
                for state in mentions_by_state.index:
                    print(f"State: {state}, Total Mentions: {int(mentions_by_state.get(state, 0))}, Normalized Mentions: {float(normalized_mentions.get(state, 0))}")
                    results[state][group_name][topic] = {
                        'total_mentions': int(mentions_by_state.get(state, 0)),
                        'mentions_per_100_comments': float(normalized_mentions.get(state, 0))
                    }
        
        return dict(results)

    def get_sentiment_by_state(self):
        """Calculate basic sentiment metrics by state"""
        positive_words = ['great', 'good', 'excellent', 'happy', 'hope']
        negative_words = ['bad', 'terrible', 'worst', 'corrupt', 'fraud']
        
        for state in self.df['state'].unique():
            state_comments = self.df[self.df['state'] == state]['0']
            
            pos_count = sum(state_comments.str.contains('|'.join(positive_words), case=False, na=False))
            neg_count = sum(state_comments.str.contains('|'.join(negative_words), case=False, na=False))
            
            total_comments = len(state_comments)
            sentiment_ratio = (pos_count - neg_count) / total_comments if total_comments > 0 else 0
            
            yield {
                'state': state,
                'sentiment_ratio': round(sentiment_ratio, 3),
                'positive_count': pos_count,
                'negative_count': neg_count,
                'total_comments': total_comments
            }

    def get_engagement_metrics(self):
        """Calculate engagement metrics by state"""
        metrics = self.df.groupby('state').agg({
            'like_count': ['mean', 'max', 'sum', 'count'],
            'reply_count': ['mean', 'sum']
        }).round(2)
        
        metrics.columns = [
            'avg_likes_per_comment',
            'max_likes',
            'total_likes',
            'comment_count',
            'avg_replies_per_comment',
            'total_replies'
        ]
        
        return metrics

    def generate_visualizations(self, keyword_analysis):
        plt.figure(figsize=(15, 10))
        
        mentions_data = []
        for state, data in keyword_analysis.items():
            for topic, keywords in data['topics'].items():
                mentions_data.append({
                    'state': state,
                    'topic': topic,
                    'mentions_per_100': keywords['mentions_per_100_comments']
                })
        
        mentions_df = pd.DataFrame(mentions_data)
        sns.barplot(data=mentions_df, x='state', y='mentions_per_100', hue='topic')
        plt.xticks(rotation=45)
        plt.title('Normalized Keyword Mentions by State')
        plt.tight_layout()
        plt.savefig('data/keyword_analysis.png')

    def get_top_comments_by_state(self, n=3):
        """Get top n comments for each state based on like count"""
        return self.df.sort_values('like_count', ascending=False).groupby('state').head(n).to_dict('records')

    def get_top_comments_by_video(self, n=3):
        """Get top n comments for each video based on like count"""
        return self.df.sort_values('like_count', ascending=False).groupby('video_id').head(n).to_dict('records')

# used to test the script
def main():
    comments_with_video = pd.read_csv('data/comments_with_video.csv')
    
    analyzer = CommentAnalyzer(comments_with_video)
    
    keyword_analysis = analyzer.analyze_keywords_by_state()
    sentiment_analysis = pd.DataFrame(list(analyzer.get_sentiment_by_state()))
    engagement_metrics = analyzer.get_engagement_metrics()
    top_comments_by_state = analyzer.get_top_comments_by_state()
    top_comments_by_video = analyzer.get_top_comments_by_video()
    
    state_summary = {}
    for state in comments_with_video['state'].unique():
        if pd.isna(state):
            state_summary[state] = {}
            continue
            
        state_summary[state] = {
            'keywords': keyword_analysis[state] if state in keyword_analysis else {},
            'sentiment': sentiment_analysis[sentiment_analysis['state'] == state].to_dict('records')[0],
            'engagement': engagement_metrics.loc[state].to_dict(),
            'top_comments': [comment for comment in top_comments_by_state if comment['state'] == state]
        }
    
    for state, data in state_summary.items():
        db.state_analysis.update_one(
            {'state': state},
            {'$set': data},
            upsert=True
        )
    
    video_comments = {}
    for comment in top_comments_by_video:
        video_id = comment['video_id']
        if video_id not in video_comments:
            video_comments[video_id] = []
        video_comments[video_id].append(comment)
    
    for video_id, comments in video_comments.items():
        db.video_analysis.update_one(
            {'video_id': video_id},
            {'$set': {'top_comments': comments}},
            upsert=True
        )
    
    existing_comment_ids = set(db.comments.distinct('comment_id'))
    new_comments = [comment for comment in comments_with_video.to_dict('records') 
                    if comment['comment_id'] not in existing_comment_ids]
    
    db.state_analysis.delete_many({})
    db.state_analysis.insert_many([{'state': k, **v} for k, v in state_summary.items()])
    
    db.video_analysis.delete_many({})
    db.video_analysis.insert_many([{'video_id': video_id, 'top_comments': comments} 
                                   for video_id, comments in video_comments.items()])
    
    #analyzer.generate_visualizations(keyword_analysis)
    
    print("Analysis complete. Data saved to MongoDB Atlas.")

if __name__ == "__main__":
    main()
