from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, urljoin

app = Flask(__name__)

# Function to search Google
def search_google(query, num_results):
    query = query.replace(" ", "+")
    url = f"https://www.google.com/search?q={query}&num={num_results}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception("Failed to fetch the search results. Status Code: {}".format(response.status_code))

    soup = BeautifulSoup(response.text, 'html.parser')
    search_results = []

    for result in soup.select(".tF2Cxc"):
        title = result.select_one(".DKV0Md").text if result.select_one(".DKV0Md") else None
        link = result.select_one("a")["href"] if result.select_one("a") else None
        snippet = result.select_one(".aCOpRe").text if result.select_one(".aCOpRe") else None

        # Fetch metadata from individual result pages
        description, keywords, favicon = fetch_metadata(link)

        if title and link:
            search_results.append({
                "title": title,
                "link": link,
                "snippet": snippet,
                "description": description,
                "keywords": keywords,
                "favicon": favicon
            })

    return search_results[:num_results]

# Function to fetch description, keywords, and favicon from individual result pages
def fetch_metadata(link):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
    }
    try:
        page_response = requests.get(link, headers=headers)
        if page_response.status_code != 200:
            return None, None, None

        page_soup = BeautifulSoup(page_response.text, 'html.parser')

        # First, check Open Graph tags for description and keywords
        description = page_soup.select_one('meta[property="og:description"]')
        keywords = page_soup.select_one('meta[property="og:keywords"]')

        # Fallback to traditional meta tags if og:description or og:keywords are not found
        if not description:
            description = page_soup.select_one('meta[name="description"]')
        if not keywords:
            keywords = page_soup.select_one('meta[name="keywords"]')

        description = description['content'] if description else None
        keywords = keywords['content'] if keywords else None

        # Fetch favicon
        favicon = page_soup.select_one('link[rel="icon"]') or page_soup.select_one('link[rel="shortcut icon"]')
        if favicon:
            # If favicon URL is relative, join it with the base URL
            favicon = favicon['href']
            parsed_url = urlparse(link)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            favicon = urljoin(base_url, favicon)

        return description, keywords, favicon
    except Exception as e:
        print(f"Error fetching metadata for {link}: {e}")
        return None, None, None

# Function to search Google Images
def search_google_images(query, num_results):
    query = query.replace(" ", "+")
    url = f"https://www.google.com/search?hl=en&tbm=isch&q={query}&num={num_results}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception("Failed to fetch the image search results. Status Code: {}".format(response.status_code))

    soup = BeautifulSoup(response.text, 'html.parser')
    image_results = []

    for result in soup.find_all('img'):
        img_src = result['src']
        if img_src and len(image_results) < num_results:
            image_results.append({"link": img_src})

    return image_results

# Flask route for search
@app.route('/search')
def search():
    query = request.args.get('q')
    num_results = int(request.args.get('n', 10))  # Default to 10 results if 'n' is not provided
    image_search = request.args.get('images', 'false').lower() == 'true'

    # Start measuring the load time
    start_time = time.time()

    try:
        if not query:
            # If no query, return instructions
            return jsonify({
                "instructions": "Please provide a search query using the 'q' parameter in the URL. For example: /search?q=your+query&n=10&images=false"
            })

        if image_search:
            results = search_google_images(query, num_results)
        else:
            results = search_google(query, num_results)

        # Calculate load time
        load_time = time.time() - start_time

        # Include the load time in the response
        return jsonify({
            "results": results,
            "load_time_seconds": load_time
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
