


import csv
import os
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google_images_download import google_images_download
import difPy  # Importing difPy for duplicate image detection

MAX_IMAGES_PER_FOLDER = 50
DD_SUFFIX = "__DD"  # Suffix for deduplicated images
def is_duplicate(image_path, all_valid_images):
    # Building difPy objects for the new image and existing images
    new_image_dif = difPy.build(image_path)
    existing_images_dif = difPy.build(all_valid_images)

    # Searching for duplicates between the new image and existing images
    search = difPy.search(new_image_dif, existing_images_dif)
    duplicates = search.result

    # If there are matches, the image is a duplicate
    return bool(duplicates)

def remove_duplicates_within_folder(folder_path):
    # Using difPy to build image collection and search for duplicates
    dif = difPy.build(folder_path)
    search = difPy.search(dif)
    duplicates = search.result  # Getting the results

    # Loop through the duplicates and remove them
    for image_id, data in duplicates.items():
        for match in data['matches']:
            duplicate_image_path = match['location']
            if os.path.exists(duplicate_image_path):
                os.remove(duplicate_image_path)
                print(f"Duplicate removed: {duplicate_image_path}")

    # Marking remaining images as deduplicated
    images = [f for f in os.listdir(folder_path) if f.endswith(".jpg")]
    for image in images:
        mark_deduplicated(os.path.join(folder_path, image))

    print(f"Completed checking folder: {folder_path}")

def mark_deduplicated(image_path):
    directory, filename = os.path.split(image_path)
    filename, ext = os.path.splitext(filename)
    
    # Check if the filename already ends with the deduplication suffix
    if not filename.endswith(DD_SUFFIX):
        new_filename = f"{filename}{DD_SUFFIX}{ext}"
        new_path = os.path.join(directory, new_filename)
        os.rename(image_path, new_path)
    else:
        null



    

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
            "limit": MAX_IMAGES_PER_FOLDER,
            "print_urls": True,
            "size": "large",
            "output_directory": output_directory,
            "image_directory": image_directory
        }

        absolute_image_paths = response.download(arguments)
        if isinstance(absolute_image_paths, dict) and query in absolute_image_paths:
            downloaded_images = absolute_image_paths[query]
        else:
            print(f"Failed to download images for {query}.")
            return

        existing_images = [os.path.join(full_directory_path, img) for img in os.listdir(full_directory_path) if os.path.isfile(os.path.join(full_directory_path, img))]

        # This list will contain all images: existing and new ones that are not duplicates.
        all_valid_images = existing_images.copy()

        for image_info in downloaded_images:
            image_url, image_path = image_info

            # Check if the image is a duplicate by comparing with all valid images.
            if is_duplicate(image_path, all_valid_images):
                os.remove(image_path)
                print(f"Duplicate image removed: {image_url}")
            else:
                all_valid_images.append(image_path)  # Add it to the list if it's not a duplicate.

    except Exception as e:
        print(f"Error for {family} {species}: {e}")

def sanitize_filename(name):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in name if c in valid_chars).strip()
def main():
    RATE_LIMIT = 3  # requests per second
    INTERVAL = 1 / RATE_LIMIT  # interval between requests in seconds

    with open('mushrooms.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        with ThreadPoolExecutor() as executor:
            dedupe_futures = []

            for row in reader:
                family = sanitize_filename(row['Family'])
                species = sanitize_filename(row['Species'])
                directory_path = f"./downloads/{family}_{species}".replace(" ", "_")

                if os.path.exists(directory_path):
                    dedupe_futures.append(executor.submit(remove_duplicates_within_folder, directory_path))

            for future in as_completed(dedupe_futures):
                future.result()

        # Resetting the CSV reader's position
        csvfile.seek(0)
        reader = csv.DictReader(csvfile)

        with ThreadPoolExecutor() as executor:
            download_futures = []
            start_time = time.time()

            for row in reader:
                family = sanitize_filename(row['Family'])
                species = sanitize_filename(row['Species'])

                download_futures.append(executor.submit(download_images, family, species))

                if len(download_futures) >= RATE_LIMIT:
                    time.sleep(max(0, INTERVAL - (time.time() - start_time)))
                    start_time = time.time()

            for future in as_completed(download_futures):
                future.result()

if __name__ == "__main__":
    main()
