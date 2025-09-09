from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
import random
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Add a secret key for session management

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
]

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

def get_headers():
    """Return random headers for each request"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0"
   }

def scrape_product(url):
    """Scrape Amazon product details using the working approach"""
    product = {
        "title": "Not found",
        "price": "Not found",
        "rating": "Not found",
        "description": "Not found",
        "details": "Not found",
        "image": "",
        "url": url
    }
    
    try:
        # Add delay to avoid being blocked
        time.sleep(1 + random.random() * 2)

        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Title
        title = soup.find("span", {"id": "productTitle"})
        product["title"] = title.get_text(strip=True) if title else "Not found"

        # Price
        price = soup.find("span", {"class": "a-price-whole"})
        if price:
            product["price"] = price.get_text(strip=True)
        else:
            # Try alternative price selectors
            price = soup.find("span", {"class": "a-offscreen"})
            product["price"] = price.get_text(strip=True) if price else "Not found"
        
        # Rating
        rating = soup.find("span", {"class": "a-icon-alt"})
        product["rating"] = rating.get_text(strip=True) if rating else "Not found"

        # Description
        description = soup.find("div", {"id": "feature-bullets"})
        if description:
            desc_text = description.get_text(strip=True)
            if len(desc_text) > 500:
                desc_text = desc_text[:500] + "..."
            product["description"] = desc_text
        else:
            product["description"] = "Not found"

        # Product details
        details = {}
        tech_details = soup.find("table", {"id": "productDetails_techSpec_section_1"})
        if tech_details:
            for row in tech_details.find_all("tr"):
                key = row.find("th").get_text(strip=True) if row.find("th") else ""
                value = row.find("td").get_text(strip=True) if row.find("td") else ""
                if key and value:
                    details[key] = value

        product_details = soup.find("table", {"id": "productDetails_detailBullets_sections1"})
        if product_details:
            for row in product_details.find_all("tr"):
                key = row.find("th").get_text(strip=True) if row.find("th") else ""
                value = row.find("td").get_text(strip=True) if row.find("td") else ""
                if key and value:
                    details[key] = value

        bullet_details = soup.find("div", {"id": "detailBullets_feature_div"})
        if bullet_details:
            items = bullet_details.find_all("span", {"class": "a-text-bold"})
            for item in items:
                key = item.get_text(strip=True).replace(":", "")
                value = item.find_next("span").get_text(strip=True) if item.find_next("span") else ""
                if key and value:
                    details[key] = value

        # Convert details dict to string
        if details:
            details_list = [f"{k}: {v}" for k, v in details.items()]
            product["details"] = "; ".join(details_list)
        else:
            product["details"] = "Not found"

        # Product image
        img = soup.find("img", {"id": "landingImage"})
        if img and img.get("src"):
            product["image"] = img["src"]
        else:
            # Try alternative image selectors
            img = soup.find("img", {"class": "a-dynamic-image"})
            product["image"] = img["src"] if img and img.get("src") else ""

    except requests.exceptions.RequestException as e:
        product["title"] = f"Error fetching product: {str(e)}"
    except Exception as e:
        product["title"] = f"Error parsing product: {str(e)}"
    
    return product

def save_to_csv(data, filename=None):
    """Save product data to CSV file"""
    if filename is None:
        filename = f"data/product_comparisons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
   
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'product_type', 'status', 'title', 'price', 
                     'rating', 'description', 'details', 'image', 'url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for product in data:
            product_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'product_type': product.get('product_type', ''),
                'status': product.get('status', ''),
                'title': product.get('title', ''),
                'price': product.get('price', ''),
                'rating': product.get('rating', ''),
                'description': product.get('description', ''),
                'details': product.get('details', ''),
                'image': product.get('image', ''),
                'url': product.get('url', '')
            }
            writer.writerow(product_data)
    
    return filename

@app.route('/', methods=['GET', 'POST'])
def index():
    products = []
    new_product_mode = False
    
    if request.method == 'POST':
        # Check if this is a submission of edited data
        if 'edited_title_2' in request.form:
            # Process edited data - only RHS (Product 2) is editable
            products = [{
                "title": request.form.get('original_title_1', ''),
                "price": request.form.get('original_price_1', ''),
                "rating": request.form.get('original_rating_1', ''),
                "description": request.form.get('original_description_1', ''),
                "details": request.form.get('original_details_1', ''),
                "image": request.form.get('original_image_1', ''),
                "url": request.form.get('original_url_1', ''),
                "status": "Accepted",
                "product_type": "Product 1"
            }, {
                "title": request.form.get('edited_title_2', ''),
                "price": request.form.get('edited_price_2', ''),
                "rating": request.form.get('edited_rating_2', ''),
                "description": request.form.get('edited_description_2', ''),
                "details": request.form.get('edited_details_2', ''),
                "image": request.form.get('original_image_2', ''),
                "url": request.form.get('original_url_2', ''),
                "status": "Edited",
                "product_type": "Product 2"
            }]

            # Save to CSV
            save_to_csv(products)
            return render_template('index.html', success=True, products=[])

        # Check if this is an Accept action
        elif 'accept' in request.form:
            # Mark both products as accepted and save to CSV
            url1 = request.form.get('original_url_1', '')
            url2 = request.form.get('original_url_2', '')

            # Get the original products data from the form
            product1 = {
                "title": request.form.get('original_title_1', ''),
                "price": request.form.get('original_price_1', ''),
                "rating": request.form.get('original_rating_1', ''),
                "description": request.form.get('original_description_1', ''),
                "details": request.form.get('original_details_1', ''),
                "image": request.form.get('original_image_1', ''),
                "url": url1,
                "status": "Accepted",
                "product_type": "Product 1"
            }

            product2 = {
                "title": request.form.get('original_title_2', ''),
                "price": request.form.get('original_price_2', ''),
                "rating": request.form.get('original_rating_2', ''),
                "description": request.form.get('original_description_2', ''),
                "details": request.form.get('original_details_2', ''),
                "image": request.form.get('original_image_2', ''),
                "url": url2,
                "status": "Accepted",
                "product_type": "Product 2"
            }

            # Save to CSV
            save_to_csv([product1, product2])
            return render_template('index.html', success=True, products=[])

        # Check if NEW button was clicked (we need to check for the hidden input)
        elif 'new_product' in request.form and request.form['new_product'] == 'true':
            url1 = request.form.get('url1', '')

            if url1:
                # Scrape only the first product
                product = scrape_product(url1)
                product['product_type'] = "Product 1"
                products.append(product)

                # Create an empty product for the second (new) product
                empty_product = {
                    "title": "",
                    "price": "",
                    "rating": "",
                    "description": "",
                    "details": "",
                    "image": "",
                    "url": "",
                    "product_type": "Product 2"
                }
                products.append(empty_product)
                new_product_mode = True

        # Otherwise, it's a new product comparison request with two URLs
        else:
            url1 = request.form.get('url1', '')
            url2 = request.form.get('url2', '')

            if url1 and url2:
                products = []
                for i, url in enumerate([url1, url2]):
                    product = scrape_product(url)
                    product['product_type'] = f"Product {i+1}"
                    products.append(product)
            elif url1:  # Only one URL provided, treat as new product mode
                product = scrape_product(url1)
                product['product_type'] = "Product 1"
                products.append(product)
                
                empty_product = {
                    "title": "",
                    "price": "",
                    "rating": "",
                    "description": "",
                    "details": "",
                    "image": "",
                    "url": "",
                    "product_type": "Product 2"
                }
                products.append(empty_product)
                new_product_mode = True
    
    return render_template('index.html', products=products, new_product_mode=new_product_mode)

@app.route('/download-csv')
def download_csv():
    # Get the most recent CSV file
    csv_files = [f for f in os.listdir('data') if f.endswith('.csv')]
    if not csv_files:
        return "No CSV files available"
    
    latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join('data', x)))
    return send_file(os.path.join('data', latest_file), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
