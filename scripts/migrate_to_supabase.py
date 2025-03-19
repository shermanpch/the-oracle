#!/usr/bin/env python3
"""
Script to migrate I Ching data from local storage to Supabase database.

This script reads text and image files from the data directory and
imports them into the Supabase iching_texts table and storage.

Requirements:
- You must have SUPABASE_URL and SUPABASE_SERVICE_KEY set in your .env file

Usage:
    python migrate_to_supabase.py [--text] [--images]

    --text:   Migrate text data
    --images: Migrate image files

    If no arguments are provided, both text and images will be migrated.
"""

import argparse
import glob
import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in your .env file"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def check_if_table_exists(table_name):
    """
    Check if a table exists in the database using a compatible query.

    Args:
        table_name: The name of the table to check

    Returns:
        bool: True if the table exists, False otherwise
    """
    try:
        # Simply try to fetch a single row with limit
        result = supabase.table(table_name).select("*").limit(1).execute()
        return True
    except Exception as e:
        # Check if the error message indicates the table doesn't exist
        error_str = str(e)
        if "relation" in error_str and "does not exist" in error_str:
            return False
        elif "PGRST" in error_str:  # PostgREST error codes
            return False
        else:
            # Re-raise unexpected errors
            print(f"Unexpected error checking table {table_name}: {str(e)}")
            return False


def migrate_texts_to_supabase():
    """
    Migrate all text files from local storage to Supabase database.
    """
    data_dir = "data"
    success_count = 0
    error_count = 0
    skipped_count = 0

    print("Checking if iching_texts table exists...")
    if not check_if_table_exists("iching_texts"):
        print("Error: The iching_texts table does not exist.")
        print("Please run scripts/create_supabase_tables.py first.")
        return False

    # Get count of existing records (informational only)
    try:
        # Try to get a rough idea of how many records exist
        existing_records = supabase.table("iching_texts").select("id").execute()
        existing_count = (
            len(existing_records.data) if hasattr(existing_records, "data") else 0
        )
        print(f"Found iching_texts table with approximately {existing_count} records.")
    except Exception as e:
        print(f"Found iching_texts table but couldn't count records: {str(e)}")

    # Dictionary to store parent texts by parent_coord
    parent_texts = {}

    print(f"Starting to migrate text files from {data_dir} directory...")

    # First pass: Find and store all parent texts
    print("Processing parent texts...")
    for parent_dir in glob.glob(f"{data_dir}/[0-9]*-[0-9]*"):
        parent_coord = os.path.basename(parent_dir)  # e.g., "0-0"
        parent_text_path = os.path.join(parent_dir, "html", "body.txt")

        if not os.path.exists(parent_text_path):
            print(f"Warning: No parent text file found at {parent_text_path}")
            continue

        try:
            with open(parent_text_path, "r", encoding="utf-8") as f:
                parent_text = f.read()

            # Store this parent text for use with child records
            parent_texts[parent_coord] = parent_text
            print(f"Found parent text for {parent_coord}")

        except Exception as e:
            print(f"Error reading parent text for {parent_coord}: {str(e)}")
            error_count += 1

    # Second pass: Process all child texts
    print("Processing child texts...")
    for parent_dir in glob.glob(f"{data_dir}/[0-9]*-[0-9]*"):
        parent_coord = os.path.basename(parent_dir)  # e.g., "0-0"
        parent_text = parent_texts.get(parent_coord)

        if not parent_text:
            print(
                f"Warning: No parent text found for {parent_coord}, skipping children"
            )
            continue

        # Find all child directories (numbered subdirectories)
        for child_dir in glob.glob(os.path.join(parent_dir, "[0-9]")):
            child_coord = os.path.basename(child_dir)  # e.g., "0", "1", etc.
            child_text_path = os.path.join(child_dir, "html", "body.txt")

            if not os.path.exists(child_text_path):
                print(f"Warning: No child text file found at {child_text_path}")
                continue

            try:
                with open(child_text_path, "r", encoding="utf-8") as f:
                    child_text = f.read()

                # Create or update the child record
                existing = (
                    supabase.table("iching_texts")
                    .select("id")
                    .eq("parent_coord", parent_coord)
                    .eq("child_coord", child_coord)
                    .execute()
                )

                if existing.data and len(existing.data) > 0:
                    # Update existing record
                    record_id = existing.data[0]["id"]
                    supabase.table("iching_texts").update(
                        {"parent_text": parent_text, "child_text": child_text}
                    ).eq("id", record_id).execute()
                    print(f"Updated child text record for {parent_coord}/{child_coord}")
                else:
                    # Insert new record
                    data = {
                        "parent_coord": parent_coord,
                        "child_coord": child_coord,
                        "parent_text": parent_text,
                        "child_text": child_text,
                    }
                    supabase.table("iching_texts").insert(data).execute()
                    print(f"Created child text record for {parent_coord}/{child_coord}")

                success_count += 1

            except Exception as e:
                print(
                    f"Error processing child text for {parent_coord}/{child_coord}: {str(e)}"
                )
                error_count += 1

    print(f"Text migration completed: {success_count} successful, {error_count} failed")
    return success_count > 0


def migrate_images_to_supabase():
    """
    Migrate all image files from local storage to Supabase storage.
    """
    data_dir = "data"
    bucket_name = "iching-images"
    success_count = 0
    error_count = 0
    skipped_count = 0

    # First, check if bucket exists
    print("Checking if storage bucket exists...")
    try:
        # Get list of buckets (works without execute())
        buckets_response = supabase.storage.list_buckets()

        # Process the response based on its type
        buckets = []
        if isinstance(buckets_response, list):
            buckets = buckets_response
        elif hasattr(buckets_response, "data"):
            buckets = buckets_response.data

        # Check if our bucket exists
        bucket_exists = False
        for bucket in buckets:
            if isinstance(bucket, dict) and bucket.get("name") == bucket_name:
                bucket_exists = True
                break
            elif hasattr(bucket, "name") and bucket.name == bucket_name:
                bucket_exists = True
                break

        if not bucket_exists:
            print(f"Bucket '{bucket_name}' does not exist. Attempting to create it...")
            # Create bucket (works without execute())
            supabase.storage.create_bucket(bucket_name)
            print(f"Created bucket: {bucket_name}")

    except Exception as e:
        print(f"Error checking/creating bucket: {str(e)}")
        print(
            "Please run scripts/create_supabase_tables.py first or create the bucket manually."
        )
        return False

    # Now upload images
    print(f"Starting to migrate image files from {data_dir} directory...")
    for img_file in glob.glob(f"{data_dir}/**/images/hexagram.jpg", recursive=True):
        try:
            path_parts = img_file.split(os.sep)
            parent_coord = path_parts[1]  # e.g., "0-1"
            child_coord = path_parts[2]  # e.g., "3"

            dest_path = f"{parent_coord}/{child_coord}/hexagram.jpg"

            # Check if file already exists
            try:
                # List files in directory (works without execute())
                files_response = supabase.storage.from_(bucket_name).list(
                    f"{parent_coord}/{child_coord}"
                )

                # Process the response based on its type
                files = []
                if isinstance(files_response, list):
                    files = files_response
                elif hasattr(files_response, "data"):
                    files = files_response.data

                # Check if our file exists
                if files and any(
                    isinstance(file, dict) and file.get("name") == "hexagram.jpg"
                    for file in files
                ):
                    print(f"Image already exists at {dest_path}. Skipping.")
                    skipped_count += 1
                    continue
            except Exception:
                # Folder probably doesn't exist, which is fine
                pass

            with open(img_file, "rb") as f:
                file_content = f.read()

            # Upload file (works without execute())
            storage_client = supabase.storage.from_(bucket_name)
            storage_client.upload(
                dest_path,
                file_content,
            )

            print(f"Migrated image: {dest_path}")
            success_count += 1

        except Exception as e:
            print(f"Error migrating image {img_file}: {str(e)}")
            error_count += 1

    print(
        f"Image migration completed: {success_count} successful, {skipped_count} skipped, {error_count} failed"
    )
    return success_count > 0


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Migrate I Ching data from local storage to Supabase."
    )
    parser.add_argument(
        "--text", action="store_true", help="Migrate text data to the database"
    )
    parser.add_argument(
        "--images", action="store_true", help="Migrate image files to storage"
    )
    args = parser.parse_args()

    # If no arguments are specified, migrate both
    migrate_text = args.text
    migrate_images = args.images
    if not (migrate_text or migrate_images):
        migrate_text = True
        migrate_images = True

    print("Starting data migration to Supabase...")

    texts_success = True
    images_success = True

    if migrate_text:
        texts_success = migrate_texts_to_supabase()

    if migrate_images:
        images_success = migrate_images_to_supabase()

    if texts_success and images_success:
        print("Migration completed successfully.")
    elif texts_success and migrate_text and not migrate_images:
        print("Text migration completed successfully.")
    elif images_success and migrate_images and not migrate_text:
        print("Image migration completed successfully.")
    elif texts_success and not images_success:
        print("Text migration completed successfully, but image migration failed.")
    elif images_success and not texts_success:
        print("Image migration completed successfully, but text migration failed.")
    else:
        print("Migration failed. Please check the errors above.")
