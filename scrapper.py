from bs4 import BeautifulSoup
import pandas as pd
import requests
import time
import re

def scrape():

    user_input = input("Enter the smartphone name: ")

    flipkart_base_url = 'http://www.flipkart.com'
    search_string = 'site:www.flipkart.com '+ user_input + ' flipkart'
    r = requests.get('https://google.com/search?q='+search_string)

    #Filter the links that directs to flipkart website
    def filter_link(s):
        pattern = re.compile(r'(https://www.flipkart.com)(.*)&sa')
        matches = pattern.finditer(s)
        if matches:
            for i in matches:
                target_link = f'{i.group(1)}{i.group(2)}'
                return target_link
        return 'invalid'

    soup = BeautifulSoup(r.content, features="html.parser")
    link_tags = soup.select('a')
    all_links = []
    valid_links = []

    for i in link_tags:
        all_links.append(i.get('href'))
    for link in all_links:
        response = filter_link(link)
        if  response != 'invalid':
            valid_links.append(response)

    product_page_absolute_url = valid_links[:1]
    print(f"product page: {product_page_absolute_url}")
    product_response = requests.get(str(product_page_absolute_url[0]))
    product_soup = BeautifulSoup(product_response.content)

    # ### Go to the 'All Reviews' Page
    review_page_relative_url = product_soup.find('a', string=re.compile(r'All.*reviews')).get('href')
    review_page_absolute_url = flipkart_base_url + review_page_relative_url
    print(f"Review Page: {review_page_absolute_url}")

    # Generate the url of positive, negative, helpful, recent and negative review page url. 
    # It ensures varities in the collected data
    negative_page_url = review_page_absolute_url.replace('&marketplace=FLIPKART', '&aid=overall&certifiedBuyer=false&sortOrder=NEGATIVE_FIRST')
    positive_page_url = review_page_absolute_url.replace('&marketplace=FLIPKART', '&aid=overall&certifiedBuyer=false&sortOrder=POSITIVE_FIRST')
    helpful_page_url = review_page_absolute_url.replace('&marketplace=FLIPKART', '&aid=overall&certifiedBuyer=false&sortOrder=MOST_HELPFUL')
    recent_page_url = review_page_absolute_url.replace('&marketplace=FLIPKART', '&aid=overall&certifiedBuyer=false&sortOrder=MOST_RECENT')

    # Send seperate get requests to them individually
    positive_page_response = requests.get(positive_page_url)
    negative_page_response = requests.get(negative_page_url)
    helpful_page_response = requests.get(helpful_page_url)
    recent_page_response = requests.get(recent_page_url)

    #Prepare the soups
    positive_page_soup = BeautifulSoup(positive_page_response.content)
    negative_page_soup = BeautifulSoup(negative_page_response.content)
    helpful_page_soup = BeautifulSoup(helpful_page_response.content)
    recent_page_soup = BeautifulSoup(recent_page_response.content)

    # get links of  5 pages out of 10 available  pages that are available in one page, 
    # for the remaining page links we have to got to the next page by clicking on Next button
    def get_all_review_page_links(soup):
        all_links_tags = soup.findAll('a', {'class':'ge-49M'})
        num_pages_to_collect = 5
        review_page_links = []
        for link in all_links_tags[:num_pages_to_collect]:
            relative_url = link.get('href')
            absolute_url = flipkart_base_url + relative_url     
            review_page_links.append(absolute_url)
        return review_page_links

    #get the review titles for the page
    def get_review_titles(soup):
        titles_tags = soup.findAll('p', {'class':'_2-N8zT'})
        for t in titles_tags:
            review_titles.append(t.text)
        return review_titles

    #get the review descriptions for the page
    def get_review_descriptions(soup):
        review_descriptions_tags = soup.findAll('div', {'class':'t-ZTKy'})
        for t in review_descriptions_tags:
            review_descriptions.append(t.get_text().replace('READ MORE', ''))
        return review_descriptions

    #get the ratings for the page
    def get_review_ratings(soup):
        review_ratings_tags = soup.findAll('div', {'class':['_3LWZlK _1rdVr6 _1BLPMq', '_3LWZlK _1BLPMq', '_3LWZlK _32lA32 _1BLPMq']})
        for t in review_ratings_tags:
            review_ratings.append(int(t.text.strip()))
        return review_ratings      

    #Generating an empty DataFrame to store the reviews
    review_titles = []
    review_descriptions = []
    review_ratings = []
    reviews_df = pd.DataFrame(columns = ['review_title', 'review_description', 'rating'])

    #Fetching only first 5 pages, roughly 50 reviews, from the page given
    def collect_data(soup):
        for link in get_all_review_page_links(soup):
            review_page_response = requests.get(link)
            review_page_soup = BeautifulSoup(review_page_response.content)
            review_titles = get_review_titles(review_page_soup)
            review_descriptions = get_review_descriptions(review_page_soup)
            review_ratings = get_review_ratings(review_page_soup)

    def append_to_dataframe():
        nonlocal reviews_df
        temp_df = pd.DataFrame({'review_title':review_titles, 'review_description':review_descriptions, 'rating':review_ratings})
        reviews_df = pd.concat([reviews_df, temp_df], axis=0)

    #Collect the positive reviews
    collect_data(positive_page_soup)
    append_to_dataframe()
    # temp_df = pd.DataFrame({'review_title':review_titles, 'review_description':review_descriptions, 'rating':review_ratings})
    # reviews_df = pd.concat([reviews_df, temp_df], axis=0)
    time.sleep(3)

    #Collect the negative reviews
    collect_data(negative_page_soup)
    append_to_dataframe()
    # temp_df = pd.DataFrame({'review_title':review_titles, 'review_description':review_descriptions, 'rating':review_ratings})
    # reviews_df = pd.concat([reviews_df, temp_df], axis=0)
    time.sleep(4)

    #Collect the helpful reviews
    collect_data(helpful_page_soup)
    append_to_dataframe()
    # temp_df = pd.DataFrame({'review_title':review_titles, 'review_description':review_descriptions, 'rating':review_ratings})
    # reviews_df = pd.concat([reviews_df, temp_df], axis=0)
    time.sleep(3)

    #Collect the recent reviews
    collect_data(recent_page_soup)
    append_to_dataframe()
    # temp_df = pd.DataFrame({'review_title':review_titles, 'review_description':review_descriptions, 'rating':review_ratings})
    # reviews_df = pd.concat([reviews_df, temp_df], axis=0)


    print(f"Total Reviews collected: {reviews_df.shape[0]}")

    reviews_df.to_csv(f'Reviews/flipkart_reviews_{user_input}.csv', index=False)
    test = pd.read_csv(f'Reviews/flipkart_reviews_{user_input}.csv')
    print(test.head())


    return user_input   #This will be use to pick the filename in app.py


#scrape()