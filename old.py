from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

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

        if title and link:
            search_results.append({
                "title": title,
                "link": link,
                "snippet": snippet
            })

    return search_results[:num_results]

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

    try:
        if image_search:
            results = search_google_images(query, num_results)
        else:
            results = search_google(query, num_results)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
