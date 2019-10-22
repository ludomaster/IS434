import datetime as dt
import json
import praw
import pandas as pd
from praw.models import MoreComments # used to ignore 'AttributeError: 'MoreComments' object has no attribute 'body''

# General docs: https://praw.readthedocs.io/en/latest/code_overview/models/subreddit.html
# Submissions docs: https://praw.readthedocs.io/en/latest/code_overview/models/submission.html
# Redditor object docs: https://praw.readthedocs.io/en/latest/code_overview/models/redditor.html
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

    
    # SUBREDDIT(S)
    subreddit = reddit.subreddit('depression+suicidewatch+singapore+SGExams')

    # KEYWORDS TODO: Put in correct keywords
    keywords = ['suicidal', 'suicide', 'stress', 'depressed', 'depression', 'sad', 'hate']

    # Each subreddit has five different ways of organizing the topics created by redditors:
    #   .hot, .new, .controversial, .top, .gilded
    # Can also use subreddit.search("KEYWORD") to get matching results
    top_submissions = subreddit.top(limit=1) # Getting top up-voted topics of all time in r/singapore

    # Dictionary of topics and its information to be used as DataFrame
    topics_dict = {"author": [],
                "title":[],
                "score":[],
                "id":[],
                "url":[],
                "comms_num": [],
                "created": [],
                "body":[]}

    # Dictionary of users and their infromation to be uased as DataFrame
    users_dict = {"author": [],
                "submissions": [],
                "comment_karma": [],
                "link_karma": [],
                "created": []} #TODO Add more information for user

    top_post_users = [] #Each user (author) from the top posts saved to check their other submissions/replies

    # Checking and saving information of top posts
    for submission in top_submissions:
        for word in keywords:

            # TODO: Remove this dataset, not needed (dont remove last row "top_post_users.append(submission.author)")
            # Include posts where title has any of keywords in it
            if word in submission.selftext: # Either .selftext (body) or .title (title of post)
                topics_dict["author"].append(submission.author)             # OP
                topics_dict["title"].append(submission.title)               # Title of post
                topics_dict["score"].append(submission.score)               # Upvotes
                topics_dict["id"].append(submission.id)                     # ID of specific submission
                topics_dict["url"].append(submission.url)                   # URL of post
                topics_dict["comms_num"].append(submission.num_comments)    # Comments on post
                topics_dict["created"].append(submission.created)           # Date of creation
                topics_dict["body"].append(submission.selftext)             # Text of post (inside the post)

                # Adds each user to a list
                top_post_users.append(submission.author)

    riskzone_users = []

    # EVALUATE EACH ACCOUNT ***THIS NEEDS A LOT OF ATTENTION/IMPROVEMENT AND INCLUDE MORE CONSTRAINTS ETC***
    for account in top_post_users:
        user = reddit.redditor(str(account))
        user_submissions = user.submissions.new()

        # Check every submission that user has made.
        for submission in user_submissions:
            #TODO: Add evaluation constraints (frequency, number of keywords, comments, minimum submissions/comments/replies etc)
            
            # If keyword is in any of users submissions, they will be printed out.
            for keyword in keywords:
                if keyword in submission.title or keyword in submission.selftext:
                    # TODO: Add more if-constraints
                    print(f"User: '{account}, keyword found: '{keyword}' title: '{submission.title}'")

                    # If user checks all flags: FLAG ACCOUNT AS RISKY
                    riskzone_users.append(user)
                else:
                    continue



    # ADD ACCOUNT DATA IF IN RISKZONE
    # TODO: Add more information? Whatever we want?
    # TODO: Add number of submissions including keywords
    for user in riskzone_users:
        users_dict["author"].append(user)
        users_dict["submissions"].append(len(list(user.submissions.new())))
        users_dict["comment_karma"].append(user.comment_karma)
        users_dict["link_karma"].append(user.link_karma)
        users_dict["created"].append(user.created_utc)



    #############################################
    # BELOW IS CODE TO RUN WHEN DATA IS COMPLETE
    #############################################

    # Convert dictionary to dataframe to make data more easily readable
    topics_data = pd.DataFrame(topics_dict)
    users_data = pd.DataFrame(users_dict)

    # Fixing column date for topics (unix time to actual time)
    _timestamp_topics = topics_data["created"].apply(get_date)
    topics_data = topics_data.assign(timestamp=_timestamp_topics)
    topics_data = topics_data.drop(columns="created")

    # Fixing column date for users (unix time to actual time)
    _timestamp_users = users_data["created"].apply(get_date)
    users_data = users_data.assign(timestamp=_timestamp_users)
    users_data = users_data.drop(columns="created")
 

    # TODO: Close each time you run if not doing tests
    #with open('reddit_table.csv', 'w+', encoding="utf-8") as file:
    #    topics_data.to_csv(file, index=False) 

    with open('reddit_riskzone_table.csv', 'w+', encoding="utf-8") as file:
        users_data.to_csv(file, index=False)

    #############################################
    # BELOW IS CODE IS FOR REPLIES
    #############################################


    # Getting particular submission
    # First, we need to obtain a submission object. There are 2 ways to do this.
    # 1) Retrieve by URL
    # 2) Retrieve by submission ID (which we happen to know, it is '50ycve')

    #Example

    submission = reddit.submission(url='https://www.reddit.com/r/singapore/comments/cfiwzc/feeling_isolated_stressed_and_depressed_more/')
    #submission = reddit.submission(id='50ycve')

    # MoreComments objects will be replaced until there are none left, as long as they satisfy the threshold.
    submission.comments.replace_more(limit=None)

    # OPTION 1 (Not that robust solution)
    # Handling comments and replies
    for comment in submission.comments:
        if isinstance(comment, MoreComments):
            continue

        # Printing comments (top level comments)
        #print("Comment: " + str(comment.body))

        # Printing reples (second level comments)
        #for reply in comment.replies:
            #print("Reply: " + str(reply.body))

    # OPTION 2 (A more robust solution)
    # Handling comments and replies (even if it's arbitrarily deep)
    # Breadth-first traversal, going through all top level comments, then all secondary comments, and so on.
    #comment_queue = submission.comments[:]
    #for comment in submission.comments.list():
        #print("=== Author: ", comment.author, "===")
        #print(comment.body)

if __name__ == "__main__":
    main()
