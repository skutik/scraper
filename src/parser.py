from bs4 import BeautifulSoup
import os
import logging

for file in os.listdir("pages/"):
    with open("pages/" + file, "r") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
        print(soup.prettify())
    break