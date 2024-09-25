import requests
from bs4 import BeautifulSoup
import re
import csv

# URL to scrape
URL = "https://example.com/products"  

def fetch_html(url):
    """Fetch HTML content of the webpage."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to retrieve the page. Status code: {response.status_code}")

def parse_html(html):
    """Parse the HTML content using BeautifulSoup and extract product data."""
    soup = BeautifulSoup(html, "html.parser")
    products = []
    
    # Find product containers (adjust based on actual HTML structure)
    product_items = soup.find_all("div", class_="product-item")
    
    for item in product_items:
        title = item.find(re.compile("h[23]")).get_text(strip=True)
        price = item.find(text=re.compile(r"\$\d+\.\d{2}"))
        link = item.find("a")["href"]
        link = f"https://example.com{link}"  # Adjust based on actual URL
        
        products.append([title, price, link])
    
    return products

def save_to_csv(products, filename="products.csv"):
    """Save product data to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Price", "Link"])
        writer.writerows(products)

def main():
    html = fetch_html(URL)
    products = parse_html(html)
    save_to_csv(products)

if __name__ == "__main__":
    main()
