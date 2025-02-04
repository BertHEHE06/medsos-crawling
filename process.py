from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from nltk.corpus import stopwords
from nltk.stem import *
from langdetect import detect
import nltk
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import Binarizer
from sklearn.metrics import jaccard_score
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random

def get_driver(chrome_driver_path, use_user_agent=False):
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    #options.add_argument("--headless")
    if use_user_agent:
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.265 Safari/537.36"
        )
    service = Service(chrome_driver_path)
    return webdriver.Chrome(service=service, options=options)

def login_twitter(driver, username, password):
    driver.get("https://twitter.com/login")
    time.sleep(5)
    try:
        username_input = driver.find_element(By.NAME, "text")
        username_input.send_keys(username)
        username_input.send_keys(Keys.RETURN)
        time.sleep(15)

        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        time.sleep(5)
    except Exception as e:
        raise Exception(f"Gagal login ke Twitter: {e}")

def login_instagram(driver, username, password):
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)
    try:
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        username_input.send_keys(username)
        password_input.send_keys(password)
        username_input.submit()
        time.sleep(5)
    except Exception as e:
        raise Exception(f"Gagal login ke Instagram: {e}")

nltk.download("stopwords")
factory = StemmerFactory()
stemmer_id = factory.create_stemmer()
stemmer_en = PorterStemmer()
def preprocess_text(text):
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'#', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.lower()
    
    try:
        language = detect(text)
    except:
        language = "unknown"
    words = text.split()
    
    if language == "id":
        stop_words = set(stopwords.words("indonesian"))
        filtered_words = [word for word in words if word not in stop_words]
        stemmed_words = [stemmer_id.stem(word) for word in filtered_words]
    elif language == "en":
        stop_words = set(stopwords.words("english"))
        filtered_words = [word for word in words if word not in stop_words]
        stemmed_words = [stemmer_en.stem(word) for word in filtered_words]
    elif language in stopwords.fileids():
        stop_words = set(stopwords.words(language))
        filtered_words = [word for word in words if word not in stop_words]
        try:
            stemmer = SnowballStemmer(language)
            stemmed_words = [stemmer.stem(word) for word in filtered_words]
        except ValueError:
            stemmed_words = filtered_words
    else:
        stemmed_words = words
    return ' '.join(stemmed_words)

def calculate_similarity(query, documents, metric='dice'):
    tfidf = TfidfVectorizer()
    tfidf_data = tfidf.fit_transform([query] + [doc[1] for doc in documents])
    binarizer = Binarizer()
    tfidf_binary = binarizer.fit_transform(tfidf_data.toarray())

    query_vec = tfidf_binary[0]
    similarities = []
    for i in range(1, len(tfidf_binary)):
        doc_vec = tfidf_binary[i]
        if metric == 'dice':
            intersection = np.sum(np.logical_and(query_vec, doc_vec))
            similarity = (2 * intersection / (np.sum(query_vec) + np.sum(doc_vec)))
        elif metric == 'jaccard':
            similarity = jaccard_score(query_vec, doc_vec)
        similarities.append((documents[i - 1][0], documents[i - 1][1], similarity))
    return similarities

def scrape_twitter(driver, keyword, max_tweets=5):
    url = f"https://twitter.com/search?q={keyword}&src=typed_query&f=live"
    driver.get(url)
    time.sleep(3)

    tweets = set()
    while len(tweets) < max_tweets:
        tweet_elements = driver.find_elements(By.XPATH, '//div[@data-testid="tweetText"]')
        for tweet in tweet_elements:
            text = tweet.text
            tweets.add((text, preprocess_text(text)))
            if len(tweets) >= max_tweets:
                break
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    return list(tweets)

def scrape_instagram(driver, keyword, max_posts=2, max_comments=5):
    url = f"https://www.instagram.com/explore/tags/{keyword.replace(' ', '').lower()}/"
    driver.get(url)
    time.sleep(5)

    post_links = set()
    while len(post_links) < max_posts:
        posts = driver.find_elements(By.XPATH, '//a[contains(@href, "/p/")]')
        post_links.update([post.get_attribute("href") for post in posts if post.get_attribute("href")])
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    comments_data = []
    for post_link in list(post_links)[:max_posts]:
        driver.get(post_link)
        time.sleep(3)
        comment_elements = driver.find_elements(By.XPATH, '//span[@class="x1lliihq x1plvlek xryxfnj x1n2onr6 x1ji0vk5 x18bv5gf x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1i0vuye xvs91rp xo1l8bm x5n08af x10wh9bi x1wdrske x8viiok x18hxmgj"]')
        
        for i, comment in enumerate(comment_elements[:max_comments], start=1):
            original_text = comment.text
            preprocessed_text = preprocess_text(original_text)
            comments_data.append((original_text, preprocessed_text))

    return comments_data

def scrape_youtube(driver, keyword, max_videos=1, max_comments=5):
    search_url = f"https://www.youtube.com/results?search_query={'+'.join(keyword.split())}"
    driver.get(search_url)
    time.sleep(3)

    video_links = []
    try:
        video_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[@id="video-title"]'))
        )
        video_links = [element.get_attribute("href") for element in video_elements[:max_videos] if element.get_attribute("href")]
    except Exception as e:
        print(f"Error fetching video links: {e}")
        return []

    all_comments = []

    for i, video_link in enumerate(video_links):
        driver.get(video_link)
        time.sleep(3)

        loaded_comments = set()
        max_scroll_attempts = 10
        for attempt in range(max_scroll_attempts):
            try:
                comment_elements = driver.find_elements(By.XPATH, '//*[@id="content-text"]')
                for element in comment_elements:
                    comment_text = element.text
                    if comment_text not in loaded_comments:
                        loaded_comments.add(comment_text)
                        if len(loaded_comments) >= max_comments:
                            break
            except Exception as e:
                print(f"Error during comment fetching: {e}")

            if len(loaded_comments) >= max_comments:
                break

            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(random.uniform(2, 4))

        for comment in list(loaded_comments)[:max_comments]:
            all_comments.append((comment, preprocess_text(comment)))

    return all_comments


if __name__ == "__main__":
    keyword = sys.argv[1]
    sources = sys.argv[2:-1]
    metric = sys.argv[-1]
    chrome_driver_path = "C:/xampp/htdocs/5_ProjectIIR_Gasal24-25/5_ProjectIIR_Gasal24-25/chromedriver-win64/chromedriver.exe"

    username_twitter = "YOUR TWITTER USERNAME"
    password_twitter = "YOUR TWITTER PASSWORD"

    username_instagram = "YOUR INSTAGRAM USERNAME"
    password_instagram = "YOUR INSTAGRAM PASSWORD"

    results = []

    try:
        driver = get_driver(chrome_driver_path)

        for source in sources:
            if source == "twitter":
                login_twitter(driver, username_twitter, password_twitter)
                tweets = scrape_twitter(driver, keyword)
                results += [("Twitter", text, preprocessed, score)
                            for text, preprocessed, score in calculate_similarity(keyword, tweets, metric)]

            elif source == "instagram":
                login_instagram(driver, username_instagram, password_instagram)
                posts = scrape_instagram(driver, keyword)
                results += [("Instagram", original, preprocessed, score)
                            for original, preprocessed, score in calculate_similarity(keyword, posts, metric)]

            elif source == "youtube":
                videos = scrape_youtube(driver, keyword)
                results += [("YouTube", text, preprocessed, score)
                            for text, preprocessed, score in calculate_similarity(keyword, videos, metric)]

            else:
                print(f"Source '{source}' tidak valid. Gunakan 'twitter', 'instagram', atau 'youtube'.")
                sys.exit(1)

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

    finally:
        if driver:
            driver.quit()

    results = sorted(results, key=lambda x: x[3], reverse=True)

    for source, original, preprocessed, similarity in results:
        if similarity > 0:
            print(f"Source: {source}")
            print(f"Original Text: {original}")
            print(f"Preprocessed Text: {preprocessed}")
            print(f"Similarity Score: {similarity:.4f}")
            print("--------------------------------------------------------------")
