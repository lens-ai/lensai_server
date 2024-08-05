import gzip
import tarfile
import os

def decompress_gz(gz_file_path, output_file_path):
    try:
        with gzip.open(gz_file_path, 'rb') as gz_file:
            with open(output_file_path, 'wb') as output_file:
                output_file.write(gz_file.read())
        print(f"Decompressed {gz_file_path} to {output_file_path}")
        return True
    except FileNotFoundError:
        print(f"File not found: {gz_file_path}")
    except IOError as e:
        print(f"I/O error while decompressing {gz_file_path}: {e}")
    except Exception as e:
        print(f"Unexpected error while decompressing {gz_file_path}: {e}")
    return False

def unpack_tar(tar_file_path, output_folder_path):
    try:
        with tarfile.open(tar_file_path, 'r') as tar:
            tar.extractall(path=output_folder_path)
        print(f"Unpacked {tar_file_path} to {output_folder_path}")
        return True
    except tarfile.TarError:
        print(f"Failed to unpack tar file: {tar_file_path}. It may be corrupted.")
    except FileNotFoundError:
        print(f"Tar file not found: {tar_file_path}")
    except IOError as e:
        print(f"I/O error while unpacking {tar_file_path}: {e}")
    except Exception as e:
        print(f"Unexpected error while unpacking {tar_file_path}: {e}")
    return False

if __name__ == "__main__":
    gz_file_path = "/tmp/lensai/stats/1/1722187285/stats.tgz"
    tar_file_path = "/tmp/lensai/stats/1/1722187285/stats.tar"
    output_folder_path = "/tmp/lensai/stats/1/1722187285/unpacked"
    
    # Decompress the .gz file
    if decompress_gz(gz_file_path, tar_file_path):
        # Unpack the .tar file
        unpack_tar(tar_file_path, output_folder_path)

