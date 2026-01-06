import os
import shutil
import tempfile
import git
from typing import List, Dict, Any
from .base import BaseExtractor

class GitLoader(BaseExtractor):
    """
    Extracts files from a Git repository.
    """
    
    def __init__(self, repo_url: str):
        super().__init__(repo_url)
        self.temp_dir = None
        
    def extract(self) -> List[Dict[str, Any]]:
        """
        Clones the repo and returns a list of file paths that are relevant (models.py, schema.sql, etc.)
        
        Returns:
            List[Dict[str, Any]]: List of discovered files.
            [
                {"file_path": "/tmp/xyz/models.py", "file_type": "django_models"},
                {"file_path": "/tmp/xyz/schema.sql", "file_type": "sql_ddl"}
            ]
        """
        if not self.temp_dir:
            self._clone_repo()
            
        discovered_files = []
        
        for root, dirs, files in os.walk(self.temp_dir):
            if ".git" in dirs:
                dirs.remove(".git")  # Don't visit .git directories
                
            for file in files:
                full_path = os.path.join(root, file)
                file_type = self._identify_file_type(file)
                
                if file_type:
                    discovered_files.append({
                        "file_path": full_path,
                        "file_type": file_type,
                        "relative_path": os.path.relpath(full_path, self.temp_dir)
                    })
                    
        return discovered_files

    def _clone_repo(self):
        """
        Clones the repository to a temporary directory.
        """
        self.temp_dir = tempfile.mkdtemp(prefix="ontologymirror_")
        print(f"Cloning {self.source} into {self.temp_dir}...")
        try:
            git.Repo.clone_from(self.source, self.temp_dir, depth=1)
        except Exception as e:
            print(f"Error cloning repository: {e}")
            raise e

    def _identify_file_type(self, filename: str) -> str:
        """
        Identifies the type of file based on its name and extension.
        """
        if filename.endswith(".sql"):
            return "sql_ddl"
        elif filename == "models.py":
            return "django_models"
        elif filename == "schema.rb":
            return "rails_schema"
        elif filename == "schema.prisma":
            return "prisma_schema"
        return None

    def cleanup(self):
        """
        Removes the temporary directory.
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
