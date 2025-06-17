# app.py
from flask import Flask, render_template, request, send_file
from scraper.google_maps_scraper import scrape_google_maps, find_instagram_handle, find_linkedin_url
import csv
import io
from datetime import datetime

app = Flask(__name__)
all_results = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global all_results
    results = []
    error = None

    if request.method == 'POST':
        city = request.form.get('city')
        keyword = request.form.get('keyword')
        if not city or not keyword:
            error = "City and keyword are required!"
        else:
            try:
                results = scrape_google_maps(city, keyword)
                all_results = results.copy()
                if not results:
                    error = "No results found."
                return render_template('results.html', listings=results, error=error)
            except Exception as e:
                print(f"Error during scraping: {e}")
                error = "Something went wrong during scraping."
                return render_template('results.html', listings=[], error=error)

    # For GET requests or if there was no POST
    return render_template('index.html')

@app.route('/filter', methods=['POST'])
def filter_results():
    global all_results
    no_website = request.form.get('no_website')
    no_instagram = request.form.get('no_instagram')
    filtered = all_results

    if no_website:
        filtered = [r for r in filtered if r['website'] == '-']
    if no_instagram:
        filtered = [r for r in filtered if r['instagram'] == '-']
    return render_template('results.html', listings=filtered, error=None)

@app.route('/download')
def download_csv():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['name', 'phone', 'website', 'instagram', 'linkedin'])
    writer.writeheader()
    writer.writerows(all_results)
    output.seek(0)
    filename = f"scraped_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True)
