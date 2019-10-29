# Used to visualize csv data (plotting)

# TODO:
# (1) Read data from reddit_riskzone_submissions_table.csv
# (2) Evaluate polarity scores of 'risk' column (-1, 0, 1)
# (3) Read data from 'reddit_riskzone_table.csv'
#  -  Summarize polarity scores for each user
#  -  Append csv-file with risk-factor for each user
# (4) TBD

# Results should contain visualizations of: 
# - overall sentiment analysis of submissions(?)
# - keyword frequency
# - users in riskzone vs. not in riskzone (percentages)

import datetime as dt
import json
from collections import defaultdict
import math
import praw
import pandas as pd
import numpy as np
import nltk
import matplotlib.pyplot as plt
import seaborn as sns
from pprint import pprint
from IPython import display
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
from nltk.tokenize import word_tokenize, RegexpTokenizer
from nltk.corpus import stopwords
from wordcloud import WordCloud

# read a list of headlines and perform lowercasing, tokenizing, and stopword removal:
def process_text(headlines):
    tokenizer = RegexpTokenizer(r'\w+')
    stop_words = stopwords.words('english')	
    tokens = []
    for line in headlines:
        toks = tokenizer.tokenize(line)
        toks = [t.lower() for t in toks if t.lower() not in stop_words]
        tokens.extend(toks)
    
    return tokens

# Instantiation
def main():
    """
    Initiation docstring
    """
	
	#read suicide-related keywords in csv
    df = pd.read_csv("reddit_riskzone_submissions_table.csv", 
			  sep=',',
			  encoding='latin-1')
    print(df)
	
	##############################################################################
    #####1. PLOTTING BAR CHART of overall sentiment analysis of submissions####
    ##############################################################################

    fig, ax = plt.subplots(figsize=(8, 8))

    counts = df.risk.value_counts(normalize=True) * 100

    sns.barplot(x=counts.index, y=counts, ax=ax)

    ax.set_xticklabels(['Negative', 'Neutral', 'Positive'])
    plt.title("Sentiment Analysis on Reddit")
    ax.set_ylabel("Percentage")
    ax.set_xlabel("Sentiment Categories")	
    #plt.show()
	##############################################################################
    #####2. PLOTTING Negative keyword frequency####
    ##############################################################################
    neg_lines = list(df[df.risk == -1].submission)
    tokenizer = RegexpTokenizer(r'\w+')
    stop_words = stopwords.words('english')
    customStopWOrds = ['iâ','one','want','anyone','today',itâ']
    stop_words.extend(customStopWOrds)
    neg_tokens = []
	
    for line in neg_lines:
        toks = tokenizer.tokenize(line)
        toks = [t.lower() for t in toks if t.lower() not in stop_words]
        neg_tokens.extend(toks)
    
    plt.style.use('ggplot')
	
    neg_freq = nltk.FreqDist(neg_tokens)
    neg_freq.most_common(20)
    print(neg_freq.most_common(20))
    y_val = [x[1] for x in neg_freq.most_common()]
    y_final = []
    for i, k, z, t in zip(y_val[0::4], y_val[1::4], y_val[2::4], y_val[3::4]):
        y_final.append(math.log(i + k + z + t))

    x_val = [math.log(i + 1) for i in range(len(y_final))]
    fig = plt.figure(figsize=(10,5))
    
    plt.xlabel("Words (Log)")
    plt.ylabel("Frequency (Log)")
    plt.title("Negative Word Frequency Distribution on Reddit")
    plt.plot(x_val, y_final)
    #plt.show()
	##############################################################################
    #####3. PLOTTING Negative keyword wordcloud####
    ##############################################################################
    neg_words = ' '.join([text for text in neg_tokens])
    wordcloud = WordCloud(width=800, height=500, random_state=21, max_font_size=110).generate(neg_words)
    plt.figure(figsize=(10, 7))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis('off')
    plt.show()
	
if __name__ == "__main__":
    main()