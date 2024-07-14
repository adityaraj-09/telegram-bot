
import telebot
import requests,json
import random
from urllib.parse import urlparse, parse_qs
import os
import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http import cookies
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pickle
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from keep_alive import keep_alive

from url_decoder import base64_decode

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    "databaseURL":"https://faceattendance-a1720-default-rtdb.firebaseio.com/",
    "storageBucket":"faceattendance-a1720.appspot.com"
})


bot = telebot.TeleBot("6370945377:AAGKbRNqeVIGxmIHC8EWufJ63pAnYrqnIdo")
movie_searchResult={}
movie_qualityLink={}
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    sent_msg=bot.send_message(message.chat.id, text="*Let me know your name*",parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg,greet)

def greet(message):
    sent_msg=bot.send_message(message.chat.id,text="Hello "+message.text+" ! Do you want me to do something??")
    bot.register_next_step_handler(sent_msg,check_negation)


def check_negation(message):
    negative_res=("no","nope","nah","sorry","No")
    if message.text in negative_res:
        bot.send_message(message.chat.id,text="Ok, have a nice day ")
    else:
        bot.send_message(message.chat.id,text="Nice, here are some commands \n start - for start \n product - for "
                                              "getting product \n quotes - for quotes \n image - for quote img\n "
                                              "upload - for adding product to database")


def fetch(id):
    import requests

    url = "https://api.themoviedb.org/3/movie/"+str(id)

    headers = {
        "accept": "application/json",
        "Authorization":os.environ["Authorization"]
    }

    response = requests.get(url, headers=headers)
    data=response.json()

    return "https://image.tmdb.org/t/p/w500"+data["poster_path"],data["release_date"]


def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies=[]
    recommended_movies_posters=[]
    date=[]
    for i in movies_list:
        movie_id=movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch(movie_id)[0])
        date.append(fetch(movie_id)[1])
    return recommended_movies,recommended_movies_posters,date


movies_dict=pickle.load(open('movie_dict.pkl','rb'))
movies=pd.DataFrame(movies_dict)
similarity=pickle.load(open('similarity.pkl','rb'))

def get_products():
    response = requests.get("https://aditya-impact.onrender.com/api/products")
    json_data = json.loads(response.text)
    image = random.choice(json_data)["image"]
    name=json_data[0]["title"]
    return [image,name]

def get_quote():
    response = requests.get("https://zenquotes.io/api/quotes")
    json_data = json.loads(response.text)
    quote = json_data[0]['q'] + "-" + json_data[0]['a']+"\n\n"+ json_data[5]['q'] + "-" + json_data[5]['a']
    return quote



def get_img():
    response = requests.get("https://zenquotes.io/api/image")
    return response.content

@bot.message_handler(commands=["quotes"])
def send_quote(message):
    quote=get_quote()
    bot.send_message(message.chat.id,text=quote)


@bot.message_handler(commands=["image"])
def send_quoteImg(message):
    quote=get_img()
    bot.send_photo(message.chat.id,photo=quote)

@bot.message_handler(commands=["product"])
def send_image(message):
    data=get_products()
    bot.send_photo(message.chat.id,data[0])

@bot.message_handler(commands=["upload"])
def image_upload(message):
    sent_msg=bot.send_message(message.chat.id,text="*select image and send in the chat!*",parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg,upload)

@bot.message_handler(content_types=["photo"])
def upload(message):
    photo_id=message.photo[-1].file_id
    file=bot.get_file(photo_id)
    downloaded_file=bot.download_file(file.file_path)
    bucket = storage.bucket()
    with open("image.jpg","wb") as new_file:
        new_file.write(downloaded_file)
        blob = bucket.blob(photo_id+".jpg")
        blob.upload_from_filename("image.jpg")
        blob.make_public()
        sent_msg=bot.send_message(message.chat.id,text="*Enter product title*",parse_mode="Markdown")
        bot.register_next_step_handler(sent_msg,title_handler,blob.public_url)


def title_handler(message,url):
    title=message.text
    sent_msg=bot.send_message(message.chat.id,text="*Enter product category*",parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg,desc_hanlder,title,url)

def desc_hanlder(message,title,url):
    cat=message.text
    sent_msg=bot.send_message(message.chat.id,text="*Enter description*",parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg,price_handler,title,url,cat)


def price_handler(message,title,url,cat):
    desc=message.text
    sent_msg = bot.send_message(message.chat.id, text="*Enter price in rupees*", parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, add_product, title, url, cat,desc)


def add_product(message,title,url,cat,desc):
    price=message.text
    data={
        "title":title,
        "userId":"adi@gmail.com",
        "desc":desc,
        "category":cat,
        "price":price,
        "location":"Delhi,India",
        "isNegotiable": True,
        "image":url
    }
    headers = {"Content-Type": "application/json; charset=utf-8"}
    response=requests.post("https://aditya-impact.onrender.com/api/addProduct",data=json.dumps(data),headers=headers)
    if (response.status_code==200):
        bot.send_message(message.chat.id,text="product has been added \n image-link:\n"+url)
    else:
        bot.send_message(message.chat.id, text="something went wrong")

@bot.message_handler(commands=["poll"])
def poll(message):
    bot.send_poll(chat_id=message.chat.id, options=["India","China","USA","Russia"],
                  question="which is the boggest country by area?")

@bot.message_handler(commands=["title"])
def set_title(message):
    bot.set_chat_title(chat_id=message.chat.id,title="Chat-Bot")


@bot.message_handler(commands=["recommend_movie"])
def rec_com(message):
    sent_msg = bot.send_message(message.chat.id, text="*enter movie name*", parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, recommend)

def rec(message):
    names, posters,date = recommend(message.text)
    for i in range(0,5):
      bot.send_photo(message.chat.id,photo=posters[i],caption=names[i]+"\nrelase-date:"+date[i])


def getSearchResults(message):
    movie=message.text.replace(' ',"+")
    url = "https://moviesmod.band/search/"+movie

# API key for ZenRows
    apikey = 'c9d58926fb5b2026a8459deb9a05fb5d2e6d7e96'

    # Parameters for the GET request
    params = {
        'url': url,
        'apikey': apikey,
        'js_render': 'true'
    }

    
    
    # Setup Selenium WebDriver
    try:
        response = requests.get('https://api.zenrows.com/v1/', params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.text
    except requests.RequestException as e:
        print(f"Error during requests to {url}: {str(e)}")

        data = None  # Ensure data is None if there was an error
        bot.send_message(message.chat.id, text="Something went wrong. Please try again later.")

# Check if data was successfully fetched
    if data:
        # Parse the HTML content
        soup = BeautifulSoup(data, 'html.parser')
        
        # Find all articles in the specified div
        movie_links = []
        articles = soup.select('div.post-cards article')
        for article in articles:
            link = article.find('a')
            if link:
                title = link.get('title', '')
                href = link.get('href', '')
                movie_links.append({'title': title, 'href': href})
        if len(movie_links) > 0:
                # Store movie search result in a global variable or database
                movie_searchResult[message.chat.id] = movie_links
                
                # Send messages to the chat bot
                bot.send_message(message.chat.id, text="Select a movie from the list below")
                for i, movie_info in enumerate(movie_links, start=1):
                    bot.send_message(message.chat.id, text=f"{i}. {movie_info['title']}")
                
                sent_msg=bot.send_message(message.chat.id, text="Enter the number of the movie you want to download")
                bot.register_next_step_handler(sent_msg, choose_movie_qualities)
                
        else:
                bot.send_message(message.chat.id, text="Sorry, movie not found!")
        # Print the list of movies
        print(movie_links)
    else:
        print("Failed to fetch or parse the data")
        bot.send_message(message.chat.id, text="Something went wrong. Please try again later.")
    
def choose_movie_qualities(message):
    movie_number = int(message.text)
    print(f"Selected movie number: {movie_number}")
    movie_links = movie_searchResult[message.chat.id]
    selected_movie = movie_links[movie_number-1]
    full_url = selected_movie["href"]
    apikey = 'c9d58926fb5b2026a8459deb9a05fb5d2e6d7e96'

    # Parameters for the GET request
    params = {
        'url': full_url,
        'apikey': apikey,
        'js_render': 'true'
    }

    
    
    # Setup Selenium WebDriver
    try:
        response = requests.get('https://api.zenrows.com/v1/', params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.text
    except requests.RequestException as e:
        print(f"Error during requests to {full_url}: {str(e)}")

        data = None  # Ensure data is None if there was an error
        bot.send_message(message.chat.id, text="Something went wrong. Please try again later.")

    
    if data:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(data, 'html.parser')
        
        # First, try to find elements by class 'GenresAndPlot__TextContainerBreakpointXL-cum89p-4'
        genres_plot_section = soup.find('div', class_='GenresAndPlot__TextContainerBreakpointXL-cum89p-4')
        
        if genres_plot_section:
            # If found, look for <hr> tag and process subsequent <h3> and <p> tags
            hr_tag = genres_plot_section.find('hr')
            if hr_tag:
                data_list = []

                # Iterate over subsequent <h3> and <p> tags
                next_tag = hr_tag.find_next_sibling()
                while next_tag:
                    if next_tag.name == 'h3':
                        title = next_tag.text.strip()
                        next_tag = next_tag.find_next_sibling('p')
                        if next_tag:
                            link = next_tag.find('a').get('href') if next_tag.find('a') else None
                            data_list.append({'title': title, 'link': link})
                        next_tag = next_tag.find_next_sibling()
                    else:
                        next_tag = next_tag.find_next_sibling()

                if len(data_list) > 0:
                    movie_qualityLink[message.chat.id] = data_list
                    sent_msg=bot.send_message(message.chat.id, text="Select a quality from the list below")
                    for i, quality_info in enumerate(data_list, start=1):
                        sent_msg=bot.send_message(message.chat.id, text=f"{i}. {quality_info['title']}")
                    bot.register_next_step_handler(sent_msg, passAds)    


            else:
                print("No <hr> tag found after 'GenresAndPlot__TextContainerBreakpointXL-cum89p-4' class.")
                bot.send_message(message.chat.id, text="No download links found for the movie.")
                return None
        else:
            # If 'GenresAndPlot__TextContainerBreakpointXL-cum89p-4' class not found, try 'thecontent clearfix'
            content_section = soup.find('div', class_='thecontent clearfix')
        
            if content_section:
                # Initialize a list to store {title, link} dictionaries
                data_list = []
                
                # Find all <h4> tags within the content_section
                h4_tags = content_section.find_all('h4', style="text-align: center;")
                
                for h4_tag in h4_tags:
                    # Extract the title from <h4>
                    title = h4_tag.text.strip()
                    
                    # Find the next <p> tag after <h4>
                    p_tag = h4_tag.find_next_sibling('p', style="text-align: center;")
                    if p_tag:
                        # Extract the link from <a> tag inside <p>
                        link = p_tag.find('a').get('href') if p_tag.find('a') else None
                        
                        # Append {title, link} dictionary to data_list
                        data_list.append({'title': title, 'link': link})
                
                if len(data_list) > 0:
                    print("Movie download links found:")
                    for quality_info in data_list:
                        print(f"{quality_info['title']}: {quality_info['link']}")

                    movie_qualityLink[message.chat.id] = data_list
                    sent_msg=bot.send_message(message.chat.id, text="Select a quality from the list below")
                    for i, quality_info in enumerate(data_list, start=1):
                        sent_msg=bot.send_message(message.chat.id, text=f"{i}. {quality_info['title']}")
                    bot.register_next_step_handler(sent_msg, passAds)    
        
            else:
                bot.send_message(message.chat.id, text="No download links found for the movie.")
                print("No <div class='thecontent clearfix'> found on the page.")
                return None
    else:
        bot.send_message(message.chat.id, text="try again!")
        return None


    
def set_cookie(name, value, minutes):
    cookie = cookies.SimpleCookie()
    expiration = datetime.now() + timedelta(minutes=int(minutes))
    cookie[name] = value
    cookie[name]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
    return cookie.output(header='').strip()

def get_query_param(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("url", [None])[0] 

def generate(url):
    full_url = "https://video-seed.xyz/api"  # Adjust the URL to your API endpoint
    headers = {
        'x-token': 'video-seed.xyz'  # Modify this as per your actual API token requirements
    }
    data = {
        'keys': get_query_param(url)
    }

    try:
        response = requests.post(full_url, headers=headers, data=data)
        response.raise_for_status()  # This will raise an exception for HTTP error codes
        return response.json()  # Returns the JSON response as a Python dictionary
    except requests.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return None
    
def passAds(message):
    i=int(message.text)
    movie_links = movie_qualityLink[message.chat.id]
    selected_movie = movie_links[i-1]
    full_url = base64_decode(selected_movie["link"])
    print(full_url)
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(full_url, headers=headers)
    soup=BeautifulSoup(response.text,"html.parser")
    divs=soup.find('a',class_="maxbutton-1 maxbutton maxbutton-fast-server-gdrive")
    
    if divs:
        
        url=divs.get('href','')
        print(url)
        
        try:
            
            apikey = 'c9d58926fb5b2026a8459deb9a05fb5d2e6d7e96'

    
            params = {
                'url': url,
                'apikey': apikey,
                'js_render': 'true'
            }
            try:
                response = requests.get('https://api.zenrows.com/v1/', params=params)
                response.raise_for_status()  # Raises an HTTPError for bad responses
                res = response.text
            except requests.RequestException as e:
                print(f"Error during requests to {full_url}: {str(e)}")

                res = None
                
            if res:      # Ensure data is None if there was an error
                soup = BeautifulSoup(res, 'html.parser')

    # Find input fields within the form
                wp_http2_value = soup.find('input', {'name': '_wp_http2'}).get('value', None)
                token_value = soup.find('input', {'name': 'token'}).get('value', None)
                form_action = soup.find('form', {'id': 'landing'}).get('action', None)

                data = {
                    '_wp_http2': wp_http2_value,
                    'token': token_value
                }

                # Using requests to send POST (alternative to navigating using Selenium)
                response = requests.post(form_action, headers=headers, data=data)
            else:
                return;  
          
            href=None
            param1=None
            param2=None
            param3=None
            if response.status_code == 200:
                # Parse the response text with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Use regex to find the script containing the desired href
                script_text = str(soup.find_all('script'))
                match = re.search(r'c\.setAttribute\("href","(https?://[^"]+)"\)', script_text)
                pattern = r"s_343\('([^']+)', '([^']+)', (\d+)\)"
                match1 = re.search(pattern, script_text)
                if match1:
                    try:
                        param1 = match1.group(1)  # First capturing group
                        param2 = match1.group(2)  # Second capturing group
                        param3 = match1.group(3)  # Third capturing group
                        print("Parameter 1:", param1)
                        print("Parameter 2:", param2)
                        print("Parameter 3:", param3)
                    except IndexError:
                        print("Attempted to access a group that does not exist.")
                else:
                    print("No match found.")

                if match:
                    href = match.group(1)
                    print("Found href:", href)
                else:
                    print("No href found in the script tags.")
            else:
                print("Failed to fetch data. Status code:", response.status_code)

            apikey = 'c9d58926fb5b2026a8459deb9a05fb5d2e6d7e96'

    # Parameters for the GET request
            params = {
                'url': href,
                'apikey': apikey,
                'js_render': 'true'
            }

            cookie_value = set_cookie(param1, param2, param3)

# Now use this cookie with requests
            
            headers = {
                'Cookie': cookie_value,
                'User-Agent': 'Mozilla/5.0'
            }
            
            # Setup Selenium WebDriver
            try:
                response = requests.get(href,headers=headers)
                response.raise_for_status()  # Raises an HTTPError for bad responses
                data = response.text
            except requests.RequestException as e:
                print(f"Error during requests to {full_url}: {str(e)}")

                data = None  # Ensure data is None if there was an error

            
# Find the meta tag with 'http-equiv' attribute set to 'refresh'
            

            rl=None
            if data:
                print(data)
                soup=BeautifulSoup(data,"html.parser")
                meta_tag = soup.find('meta', attrs={'http-equiv': 'refresh'})

            # Extract the URL from the 'content' attribute
                if meta_tag and 'content' in meta_tag.attrs:
                    content = meta_tag['content']
                    rl = content.split(';url=')[-1]
                    print("Redirect URL:", rl)
                else:
                    print("No redirect meta tag found.")

            params = {
                'url': rl,
                'apikey': apikey,
                'js_render': 'true'
            }
            final_res=None
            try:
                response = requests.get('https://api.zenrows.com/v1/', params=params)
                response.raise_for_status()  # Raises an HTTPError for bad responses
                final_res = response.text
            except requests.RequestException as e:
                print(f"Error during requests to {full_url}: {str(e)}")

                final_res = None

            print(final_res)              
            soup=BeautifulSoup(final_res,"html.parser")      
            atags=soup.select('.text-center a')
            if atags:
    # Get the href attribute of the first <a> tag
                instant_download_links = [a['href'] for a in atags if "Instant Download" in a.text.strip()]
                if instant_download_links[0]:
                    first_href = instant_download_links[0]
                    print("final_link",instant_download_links[0])
                    result=generate(first_href)
                    if result:

                        markup = InlineKeyboardMarkup()
                        button = InlineKeyboardButton(text="Download Now", url=result['url'])
                        markup.add(button)

                        # Sending a card message with a button
                        bot.send_message(
                            message.chat.id,
                            f"🎬 <b>Download Movie: {result['name']} </b>\nCheck out this amazing movie! 🍿",
                            parse_mode='HTML',
                            reply_markup=markup
                        )
                        print("The href of the first <a> tag in '.text-center':", first_href)
                else:
                    markup = InlineKeyboardMarkup()
                    button = InlineKeyboardButton(text="Download Now", url=atags[0]['href'])
                    markup.add(button)

                        # Sending a card message with a button
                    bot.send_message(
                            message.chat.id,
                            f"🎬 <b>Download Movie:</b>\nCheck out this amazing movie! 🍿",
                            parse_mode='HTML',
                            reply_markup=markup
                        )
            else:
                print("No <a> tags found in '.text-center'") 
                       
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}") 

    else:
        bot.send_message(message.chat.id,text="Something went wrong")    

    

@bot.message_handler(commands=["download_movie"])
def download_movie(message):
    sent_msg = bot.send_message(message.chat.id, text="*enter movie name*", parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, getSearchResults)
keep_alive()
bot.infinity_polling()
