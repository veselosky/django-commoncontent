import sqlite3

import nltk
from django.utils.html import strip_tags
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer


def init():
    "Initialize the search DB"
    # Create FTS5 table
    conn = sqlite3.connect("search.db")
    conn.execute(
        """CREATE VIRTUAL TABLE article_fts USING FTS5(
            title,
            description,
            body,
            tokenize='porter unicode61 remove_diacritics 2'
        )
        """
    )


def prepare(text):
    "Prepare a text to be added to the index"

    nltk.download("stopwords")

    # Normalize the text
    text = strip_tags(text)
    text = text.lower().strip()

    # Tokenize the text
    tokens = nltk.word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    tokens = [token for token in tokens if token not in stop_words]

    # Stem the tokens
    stemmer = SnowballStemmer("english")
    tokens = [stemmer.stem(token) for token in tokens]
    return tokens


import sqlite3


# Define tokenizer function
def my_tokenizer(text):
    # Normalize text
    text = text.lower()

    # Tokenize text
    tokens = text.split()

    # Remove stopwords
    stop_words = {"a", "an", "the", "and", "or", "but"}
    tokens = [token for token in tokens if token not in stop_words]

    # Stem tokens
    stemmer = SnowballStemmer("english")
    tokens = [stemmer.stem(token) for token in tokens]

    return tokens
