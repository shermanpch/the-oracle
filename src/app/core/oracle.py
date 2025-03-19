import os

from src.utils.supabase_client import get_supabase_client


class Oracle:
    def __init__(self, data_source="supabase"):
        """
        Initialize an Oracle instance.

        Args:
            data_source (str): The source of data ('local' or 'supabase')
        """
        self.data_source = data_source
        self.data_dir = "data/" if data_source == "local" else None

        if data_source == "supabase":
            self.supabase = get_supabase_client()

    def input(self, first, second, third):
        """
        Set the input values that determine the coordinate-based file paths.

        These input values will be used to compute:
            - first_cord: first % 8
            - second_cord: second % 8
            - third_cord: third % 6

        Args:
            first (int): The first integer value.
            second (int): The second integer value.
            third (int): The third integer value.
        """
        self.first = first
        self.second = second
        self.third = third

    def convert_to_cord(self):
        """
        Convert the input values to coordinate values using modulo arithmetic.

        The conversion rules are:
            - first_cord = first % 8
            - second_cord = second % 8
            - third_cord = third % 6

        These computed coordinates are used to construct the directory paths for retrieving files.
        """
        self.first_cord = self.first % 8
        self.second_cord = self.second % 8
        self.third_cord = self.third % 6

    def get_parent_directory(self):
        """
        Get the parent directory or identifier based on the computed first and second coordinates.
        """
        if self.data_source == "local":
            # Original local file logic
            parent_dir = os.path.join(
                self.data_dir, f"{self.first_cord}-{self.second_cord}"
            )
            if not os.path.exists(parent_dir):
                raise FileNotFoundError(f"Parent directory {parent_dir} not found.")
            return parent_dir
        else:
            # Just return the identifier for Supabase
            return f"{self.first_cord}-{self.second_cord}"

    def get_child_directory(self):
        """
        Get the child directory or identifier based on the computed third coordinate.
        """
        if self.data_source == "local":
            # Original local file logic
            child_dir = os.path.join(self.get_parent_directory(), str(self.third_cord))
            if not os.path.exists(child_dir):
                raise FileNotFoundError(f"Child directory {child_dir} not found.")
            return child_dir
        else:
            # Return just the child coord number for Supabase
            return str(self.third_cord)

    def get_parent_text(self):
        """
        Retrieve and read the parent text from local files or Supabase.
        """
        if self.data_source == "local":
            # Local file logic for parent text
            parent_dir = self.get_parent_directory()
            file_path = os.path.join(parent_dir, "html", "body.txt")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Parent text file not found at {file_path}.")

            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        else:
            # Supabase logic - fetch parent_text from the 'iching_texts' table
            try:
                parent_coord = self.get_parent_directory()
                child_coord = self.get_child_directory()

                response = (
                    self.supabase.table("iching_texts")
                    .select("parent_text")
                    .eq("parent_coord", parent_coord)
                    .eq("child_coord", child_coord)
                    .execute()
                )

                if response.data and len(response.data) > 0:
                    return response.data[0]["parent_text"]
                else:
                    print(f"No parent text found for {parent_coord}/{child_coord}")
                    return None
            except Exception as e:
                print(f"Error fetching parent text from Supabase: {e}")
                return None

    def get_child_text(self):
        """
        Retrieve and read the child text from local files or Supabase.
        """
        if self.data_source == "local":
            # Local file logic for child text
            child_dir = self.get_child_directory()
            file_path = os.path.join(child_dir, "html", "body.txt")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Child text file not found at {file_path}.")

            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        else:
            # Supabase logic - fetch child_text from the 'iching_texts' table
            try:
                parent_coord = self.get_parent_directory()
                child_coord = self.get_child_directory()

                response = (
                    self.supabase.table("iching_texts")
                    .select("child_text")
                    .eq("parent_coord", parent_coord)
                    .eq("child_coord", child_coord)
                    .execute()
                )

                if response.data and len(response.data) > 0:
                    return response.data[0]["child_text"]
                else:
                    print(f"No child text found for {parent_coord}/{child_coord}")
                    return None
            except Exception as e:
                print(f"Error fetching child text from Supabase: {e}")
                return None

    def get_image_path(self, directory):
        """
        Retrieve the path to the image file from local files or Supabase.
        """
        if self.data_source == "local":
            # Original local file logic
            image_path = os.path.join(directory, "images", "hexagram.jpg")
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found in {image_path}.")
            return image_path
        else:
            # For Supabase, return the URL to the image in Storage
            try:
                bucket_name = "iching-images"
                parent_coord = self.get_parent_directory()
                child_coord = self.get_child_directory()
                image_path = f"{parent_coord}/{child_coord}/hexagram.jpg"

                response = self.supabase.storage.from_(bucket_name).get_public_url(
                    image_path
                )
                return response
            except Exception as e:
                print(f"Error getting image URL from Supabase: {e}")
                return None
