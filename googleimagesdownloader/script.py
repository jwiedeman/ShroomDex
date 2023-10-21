import csv
import os
import string
import time
from google_images_download import google_images_download
from concurrent.futures import ThreadPoolExecutor, as_completed


MAX_IMAGES_PER_FOLDER = 500

def sanitize_filename(name):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    sanitized_name = ''.join(c for c in name if c in valid_chars)
    return sanitized_name.strip()

def download_images(family, species):
    try:
        family = sanitize_filename(family)
        species = sanitize_filename(species)
        query = f"{family} {species}"
        image_directory = f"{family}_{species}".replace(" ", "_")
        output_directory = "./downloads"

        full_directory_path = os.path.join(output_directory, image_directory)

        # If directory exists and has enough images, skip download
        if os.path.exists(full_directory_path):
            images = [f for f in os.listdir(full_directory_path) if os.path.isfile(os.path.join(full_directory_path, f))]
            if len(images) >= MAX_IMAGES_PER_FOLDER:
                print(f"Skipping {query}, {len(images)} images already present.")
                return

        response = google_images_download.googleimagesdownload()
        arguments = {
            "keywords": query,
            "format": "jpg",
            "limit": 10,
            "print_urls": True,
            "size": "large",
            "output_directory": output_directory,
            "image_directory": image_directory
        }

        paths = response.download(arguments)
        print(f"Downloaded images for {query}.")

    except Exception as e:
        print(f"Error for {family} {species}: {e}")

def main():
    RATE_LIMIT = 1  # requests per second
    INTERVAL = 5 / RATE_LIMIT  # interval between requests in seconds

    # This loop will continue indefinitely
    while True:
        with open('mushrooms.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            with ThreadPoolExecutor() as executor:
                futures = []
                start_time = time.time()  # Remember the start time

                for row in reader:
                    family = row['Family']
                    species = row['Species']

                    futures.append(executor.submit(download_images, family, species))

                    # Rate limiting
                    if len(futures) >= RATE_LIMIT:
                        # If we've reached the max number of requests per second, we wait
                        time.sleep(max(0, INTERVAL - (time.time() - start_time)))
                        # Then reset the start time for the next interval
                        start_time = time.time()

                # Wait for all the scheduled tasks to finish
                for future in as_completed(futures):
                    future.result()  # You can handle task results/errors here if needed

        print("Finished processing the CSV file. Restarting...")
        # Optional: sleep for a while before starting over with the CSV to prevent hammering the server
        time.sleep(10)

if __name__ == "__main__":
    main()

