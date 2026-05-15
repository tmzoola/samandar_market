import shutil
from pathlib import Path


def collect_static():
    dest_path = Path("/app/statics")  # Fixed destination path for Docker

    # Sources to copy - using Path objects
    sources = {
        "sqladmin": Path("/usr/local/lib/python3.11/site-packages/sqladmin/statics"),
        "starlette_admin": Path(
            "/usr/local/lib/python3.11/site-packages/starlette_admin/statics"
        ),
    }

    # Create destination directory if it doesn't exist
    dest_path.mkdir(exist_ok=True, parents=True)

    # Copy each source
    for name, source_path in sources.items():
        if source_path.exists():
            dest_dir = dest_path / name
            print(f"Copying {name} static files from {source_path} to {dest_dir}")

            # Remove existing directory if it exists
            if dest_dir.exists():
                shutil.rmtree(dest_dir)

            # Copy new files
            shutil.copytree(source_path, dest_dir)
            print(f"✓ Successfully copied {name} static files")
        else:
            print(f"⚠ Source not found: {source_path}")
            # List available paths for debugging
            print("Available paths in /usr/local/lib/python3.11/site-packages/:")
            try:
                site_packages = Path("/usr/local/lib/python3.11/site-packages/")
                if site_packages.exists():
                    for item in site_packages.iterdir():
                        if item.is_dir() and "admin" in item.name.lower():
                            print(f"  - {item}")
            except Exception as e:
                print(f"Error listing directory: {e}")


if __name__ == "__main__":
    collect_static()
