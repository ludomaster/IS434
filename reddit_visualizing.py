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
import matplotlib.dates as mdates
import seaborn as sns
from pprint import pprint
from IPython import display
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
from nltk.tokenize import word_tokenize, RegexpTokenizer
from nltk.corpus import stopwords
from wordcloud import WordCloud
from nltk.stem import PorterStemmer

ps = PorterStemmer()

from nltk.corpus import wordnet as wn
def get_lemma(word):
    lemma = wn.morphy(word)
    if lemma is None:
        return word
    else:
        return lemma
    
from nltk.stem.wordnet import WordNetLemmatizer
def get_lemma2(word):
    return WordNetLemmatizer().lemmatize(word)

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

def prepare_text_for_lda(text):
    tokens = tokenize(text)
    tokens = [token for token in tokens if len(token) > 4]
    tokens = [token for token in tokens if token not in en_stop]
    tokens = [get_lemma(token) for token in tokens]
    return tokens
	
# Instantiation
def main():
    """
    Initiation docstring
    """
	
    # Change to whatever you want to plot from
    subreddit = "depression"

	#read suicide-related keywords in csv
    #df = pd.read_csv(f"subreddits/{subreddit}/reddit_depression_submissions.csv", 
			  #sep=',',
			  #encoding='latin-1')
    df = pd.concat(map(pd.read_csv, ['subreddits/depression/reddit_depression_submissions.csv', 
         'subreddits/foreveralone/reddit_foreveralone_submissions.csv',
		 'subreddits/offmychest/reddit_offmychest_submissions.csv',
		 'subreddits/singapore/reddit_singapore_submissions.csv',
		 'subreddits/suicidewatch/reddit_suicidewatch_submissions.csv']))
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
    customStopWOrds = ['iâ','one','want','anyone','today','itâ','suicidal','depressed','would','get','make','really','else','even',
       'ever','know','think','day','much','going','feeling','person','died','everyone','dead','everything','feel','like',
	   'life','someone','always','still','way','sometimes','things','thoughts','something','every','back','years']
    stop_words.extend(customStopWOrds)
    neg_tokens = []
	
    for line in neg_lines:
        toks = tokenizer.tokenize(line)
        toks = [t.lower() for t in toks if t.lower() not in stop_words]
        #toks = [ps.stem(t) for t in toks]
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
    #tokenized_data = []
    #for text in neg_lines:
        #tokenized_data.append(clean_text(text))
	
	#LDA with Gensim
    #from gensim import corpora
    #dictionary = corpora.Dictionary(tokenized_data)
    #corpus = [dictionary.doc2bow(text) for text in tokenized_data]
    #import pickle
    #pickle.dump(corpus, open('corpus.pkl', 'wb'))
    #dictionary.save('dictionary.gensim')
	
    #import gensim
    #NUM_TOPICS = 5
    #ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics = NUM_TOPICS, id2word=dictionary, passes=15)
    #ldamodel.save('model5.gensim')
    #topics = ldamodel.print_topics(num_words=4)
    #for topic in topics:
       #print(topic)
	
if __name__ == "__main__":
    main()