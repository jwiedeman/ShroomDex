import os
from imagededup.methods import PHash
from imagededup.utils import plot_duplicates
import shutil
def find_image_folders(parent_directory):
    """
    Find all folders containing images in the parent directory.
    """
    image_folders = []
    for foldername, subfolders, filenames in os.walk(parent_directory):
        for filename in filenames:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_folders.append(foldername)
                break  # no need to continue checking other files in this folder
    return image_folders


def find_and_remove_duplicates(image_directory):
    """
    Find duplicate images in a given directory and remove them.
    """
    phasher = PHash()

    # Generate encodings for all images in the image directory
    encodings = phasher.encode_images(image_dir=image_directory)

    # Find duplicates using the generated encodings
    duplicates = phasher.find_duplicates(encoding_map=encodings)

    # Remove duplicates for a file that has duplicates
    for original, duplicate_list in duplicates.items():
        if duplicate_list:  # Check if current file has duplicates
            print(f"Found duplicates for file: {original}")
            for duplicate in duplicate_list:
                duplicate_file_path = os.path.join(image_directory, duplicate)
                try:
                    os.remove(duplicate_file_path)
                    print(f"Deleted: {duplicate}")
                except Exception as e:
                    print(f"Error deleting file {duplicate}: {str(e)}")
    else:  # No duplicates were found
        print("No duplicates found in this directory.")


def main():
    parent_directory = 'C:\\Users\\joshu\\Documents\\MYCOVISION\\googleimagesdownloader\\downloads'

    # Find all image folders
    image_folders = find_image_folders(parent_directory)

    # Find and remove duplicates in each folder
    for image_folder in image_folders:
        print(f'Processing folder: {image_folder}')
        find_and_remove_duplicates(image_folder)

if __name__ == "__main__":
    main()

