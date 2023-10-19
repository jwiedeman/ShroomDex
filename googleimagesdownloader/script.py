import csv
import os
import string
import time
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from google_images_download import google_images_download


MAX_IMAGES_PER_FOLDER = 50
DUPLICATE_THRESHOLD = 0.6  # Similarity threshold

def remove_duplicates_within_folder(folder_path):
    try:
        print(f"Checking for duplicates in folder {folder_path}...")

        images = os.listdir(folder_path)
        for i in range(len(images)):
            for j in range(i+1, len(images)):
                image1_path = os.path.join(folder_path, images[i])
                image2_path = os.path.join(folder_path, images[j])

                # Continue if either file does not exist
                if not os.path.exists(image1_path) or not os.path.exists(image2_path):
                    continue

                image1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
                image2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)

                # Continue if either image couldn't be read (e.g., if they're not valid image files)
                if image1 is None or image2 is None:
                    continue

                # Determine the larger image
                if image1.size < image2.size:
                    image1, image2 = image2, image1  # Swap so image1 is always the larger image
                
                # Ensure image2 is not larger than image1
                if image1.shape[0] < image2.shape[0] or image1.shape[1] < image2.shape[1]:
                    # Resize image2 to ensure it's smaller than image1
                    image2 = cv2.resize(image2, (min(image1.shape[1], image2.shape[1]), min(image1.shape[0], image2.shape[0])))

                # Compare the larger image with the smaller one using matchTemplate
                result = cv2.matchTemplate(image1, image2, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                
                # If the images are nearly identical, remove the second one
                if max_val > DUPLICATE_THRESHOLD:
                    print(f"Duplicate found: {image1_path,images[j]}")
                    os.remove(image2_path)

    except Exception as e:
        print(f"Error occurred during duplicate removal in folder {folder_path}: {e}")



def process(img):
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(img_gray, (43, 43), 21)

def confidence(img1, img2):
    res = cv2.matchTemplate(process(img1), process(img2), cv2.TM_CCOEFF_NORMED)
    return res.max()

def is_duplicate(new_image_path, existing_images):
    new_image = cv2.imread(new_image_path)
    for existing_image_path in existing_images:
        existing_image = cv2.imread(existing_image_path)
        conf = confidence(new_image, existing_image)
        if conf > DUPLICATE_THRESHOLD:
            return True
    return False

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

def main():
    RATE_LIMIT = 3  # requests per second
    INTERVAL = 1 / RATE_LIMIT  # interval between requests in seconds

    # This loop will continue indefinitely
    while True:
        with open('mushrooms.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            with ThreadPoolExecutor() as executor:
                futures = []
                start_time = time.time()  # Remember the start time

                for row in reader:
                    family = sanitize_filename(row['Family'])
                    species = sanitize_filename(row['Species'])
                    directory_path = f"./downloads/{family}_{species}".replace(" ", "_")

                    # If the folder exists, we check for internal duplicates
                    if os.path.exists(directory_path):
                        futures.append(executor.submit(remove_duplicates_within_folder, directory_path))
                    else:
                        # If the folder doesn't exist, or if you want to download new images anyway, 
                        # we initiate the download process
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

        # Optional: sleep for a while before starting over with the CSV to prevent hammering the server
        time.sleep(10)


if __name__ == "__main__":
    main()
