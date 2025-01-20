# Youtube Comment Analysis Pipeline

  
  

1. **Initial Channel Scraping (Every ~6 hours via crontab)**

```mermaid

graph TD

A[Crontab] --> B[index.js]

B --> C[Puppeteer Browser]

C --> D[YouTube Channel Pages]

D --> E[Video Data]

E --> F[temp/*_videos.json]

```

  

2. **Video Processing Stream (Continuous)**

```mermaid

graph TD

A[process_stream.py] --> B[Watchdog Observer]

B --> C[VideoDataHandler]

C --> D[Detect new *_videos.json]

D --> E[Filter target_keyword-related videos]

E --> F[Update master_videos.csv]

E --> G[video_data MongoDB ]

E --> H[Trigger comment scrape]

```

  

3. **Comment Scraping Flow**

```mermaid

graph TD

A[process_stream.py] --> B[scrape_comments function]

B --> C[comment_scrape.js]

C --> D[Puppeteer with MITM Proxy]

D --> E[xhr_scrape_ds.py intercepts]

E --> F[Process XHR responses]

F --> G[Save to CSV]

G --> H[Move to data/channel_id/video_id/]

```

  

4. **Analysis Pipeline**

```mermaid

graph TD

A[analysis.py] --> B[Load all data]

B --> C[Join with channel-to-state mapping]

C --> D[CommentAnalyzer]

D --> E[Keyword analysis]

D --> F[Sentiment analysis]

D --> G[Engagement metrics]

E & F & G --> H[MongoDB collections]

```

  

1. **Data Collection**:

- `index.js` scrapes channel video listings periodically

- `process_stream.py` watches for new video data and manages the pipeline

- `comment_scrape.js` + `xhr_scrape_ds.py` handle comment collection

  

2. **Data Processing**:

- Videos are filtered for election-related content

- Comments are processed and organized by channel/video

- Geographic attribution is maintained throughout

  

3. **Analysis**:

- `analysis.py` aggregates all data

- `comment_analysis.py` provides specialized content analysis

- Results are stored in MongoDB for the frontend to access

  

4. **MongoDB Collections**:

- `video_data`: Raw video information

- `comments_with_video`: Processed comments with video context

- `state_analysis`: State-level aggregated metrics

- `video_analysis`: Video-level analysis results