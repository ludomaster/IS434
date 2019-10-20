import datetime as dt
import praw
import json
import pandas as pd
from praw.models import MoreComments # used to ignore 'AttributeError: 'MoreComments' object has no attribute 'body''

# General docs: https://praw.readthedocs.io/en/latest/code_overview/models/subreddit.html
# Submissions docs: https://praw.readthedocs.io/en/latest/code_overview/models/submission.html
# Comments docs: https://praw.readthedocs.io/en/latest/code_overview/models/comment.html

CLIENT_ID = 'YOUR PERSONAL USE SCRIPT (14 CHARS)'
CLIENT_SECRET = 'YOUR SECRET KEY (27 CHARS)'
USER_AGENT = 'YOUR APP NAME'
USERNAME = 'YOUR REDDIT USERNAME'
PASSWORD = 'YOUR REDDIT PASSWORD'

def get_date(created):
    """
    Converts into correct datetime format
    """
    return dt.datetime.fromtimestamp(created)

# Instantiation
def main():
    """
    Initiation docstring
    """

    credentials = {}
    credentials['CLIENT_ID'] = CLIENT_ID
    credentials['CLIENT_SECRET'] = CLIENT_SECRET
    credentials['USER_AGENT'] = USER_AGENT
    credentials['USERNAME'] = USERNAME
    credentials['PASSWORD'] = PASSWORD

    # Use this first time (with your credentials in the start) to initialize your json file
    #with open("reddit_credentials.json", "w") as file:
    #    json.dump(credentials, file)

    # Use this after initializing your credentials
    with open("reddit_credentials.json", "r") as file:
        creds = json.load(file)

    # Initiate with credentials (you may have to comment this out when first initializing your json file)
    reddit = praw.Reddit(client_id=creds["CLIENT_ID"], \
                        client_secret=creds["CLIENT_SECRET"], \
                        user_agent=creds["USER_AGENT"], \
                        username=creds["USERNAME"], \
                        password=creds["PASSWORD"])

    # TODO: Add several of subreddits
    # subreddits = reddit.subreddit('singapore+suicidewatch+askreddit') ie, hardcoding our subs.
    subreddit = reddit.subreddit('singapore')

    # Each subreddit has five different ways of organizing the topics created by redditors:
    #   .hot, .new, .controversial, .top, .gilded
    # Can also use subreddit.search("KEYWORD") to get matching results
    top_subreddits = subreddit.top(limit=10) # Getting top 100 up-voted topics of all time in r/singapore

    topics_dict = { "author": [],
                "title":[],
                "score":[],
                "id":[], "url":[],
                "comms_num": [],
                "created": [],
                "body":[]}

    # Checking information of top 10 posts in r/singapore
    for submission in top_subreddits:
        topics_dict["author"].append(submission.author)
        topics_dict["title"].append(submission.title)
        topics_dict["score"].append(submission.score)
        topics_dict["id"].append(submission.id)
        topics_dict["url"].append(submission.url)
        topics_dict["comms_num"].append(submission.num_comments)
        topics_dict["created"].append(submission.created)
        topics_dict["body"].append(submission.selftext)

    # Convert dictionary to dataframe to make data more easily readable
    topics_data = pd.DataFrame(topics_dict)

    # Fixing column date. We define it, call it, and join the new column to the dataset.
    _timestamp = topics_data["created"].apply(get_date)
    topics_data = topics_data.assign(timestamp = _timestamp)

    # TODO: Close each time you run if not doing tests
    # Opens (or creates) the csv file and writes data to each column. Easily done with pandas .to_csv function.
    with open('reddit_table.csv', 'w+', encoding="utf-8") as file:
        topics_data.to_csv(file, index=False) 

    ########################################################################################################
    # Getting particular submission
    # First, we need to obtain a submission object. There are 2 ways to do this.
    # 1) Retrieve by URL
    # 2) Retrieve by submission ID (which we happen to know, it is '50ycve')

    submission = reddit.submission(url='https://www.reddit.com/r/singapore/comments/cfiwzc/feeling_isolated_stressed_and_depressed_more/')
    #submission = reddit.sumission(id='50ycve')

    # MoreComments objects will be replaced until there are none left, as long as they satisfy the threshold.
    submission.comments.replace_more(limit=None)

    # OPTION 1 (Not that robust solution)
    # Handling comments and replies
    for comment in submission.comments:
        if isinstance(comment, MoreComments):
            continue

        # Printing comments (top level comments)
        print("Comment: " + str(comment.body))

        # Printing reples (second level comments)
        for reply in comment.replies:
            print("Reply: " + str(reply.body))

    # OPTION 2 (A more robust solution)
    # Handling comments and replies (even if it's arbitrarily deep)
    # Breadth-first traversal, going through all top level comments, then all secondary comments, and so on.
    comment_queue = submission.comments[:]
    for comment in submission.comments.list():
        print("=== Author: ", comment.author, "===")
        print(comment.body)

if __name__ == "__main__": 
    main()
