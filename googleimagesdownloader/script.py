import csv
import os
import string
from google_images_download import google_images_download

def sanitize_filename(name):
    # Remove invalid characters
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    sanitized_name = ''.join(c for c in name if c in valid_chars)
    # Remove leading/trailing white spaces
    sanitized_name = sanitized_name.strip()
    
    return sanitized_name

def download_images(family, species):
    try:
        # Sanitize family and species names for safe file naming
        family = sanitize_filename(family)
        species = sanitize_filename(species)

        # Combine family and species with a space for the query
        query = f"{family} {species}"
        
        # Remove spaces for folder naming
        image_directory = f"{family}_{species}".replace(" ", "_")
        
        # Set the base output directory to 'downloads'
        output_directory = "./downloads"

        # Creating object
        response = google_images_download.googleimagesdownload()
        
        # Defining the arguments for the image download
        arguments = {
            "keywords": query,
            "format": "jpg",
            "limit": 50,  # As per your request
            "print_urls": True,  # Optionally print the image file urls
            "size": "large",
            "output_directory": output_directory,  # Base directory
            "image_directory": image_directory  # The library will create a subdirectory with this name
        }

        # Try to download images
        response.download(arguments)
    except Exception as e:
        print(f"An error occurred with {family} {species}: {e}")

# Function to read the CSV and initiate the image downloads
def main():
    with open('mushrooms.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                family = row['Family']
                species = row['Species']
                download_images(family, species)
            except Exception as e:
                print(f"An error occurred while processing the row: {e}")

# Run the main function
if __name__ == "__main__":
    main()
