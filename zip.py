import zipfile, os, click
from datetime import datetime as dt
from cryptography.fernet import Fernet
from werkzeug.security import (check_password_hash,
                               generate_password_hash)
# Importing necessary libraries:
# - `zipfile` for handling ZIP files.
# - `os` for interacting with the file system.
# - `click` for creating command-line interface (CLI) commands.
# - `datetime` for working with timestamps.
# - `cryptography.fernet` for encryption/decryption.
# - `werkzeug.security` for password hashing and verification.

folder = "ENC"
zip_filename = "encrypted.zip"
# Specifying the default folder for encrypted files and the default ZIP filename.

@click.command()
@click.argument("command", type=click.Choice(["create", "decrypt"]))
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option("-pw", help="Enter a password for accessing zipfiles",
              hide_input=True,
              prompt="Enter a password for accessing zipfiles")
def cli(command, files, pw):
    # Main function to handle the CLI commands: "create" for encryption and "decrypt" for decryption.
    # Accepts:
    # - `command`: Either "create" or "decrypt".
    # - `files`: List of file paths to process.
    # - `pw`: Password provided by the user.

    if not os.path.exists(folder):
        os.mkdir(folder)
        # Creates the ENC folder if it doesn't already exist.

    pw_path = folder + os.sep + "password.txt"
    # Path to store the hashed password.

    if command == "create":
        # If the "create" command is selected:

        pw_lower = pw.lower()
        # Converts the password to lowercase for consistency.
        pw_gen = generate_password_hash(pw_lower)
        # Hashes the password for secure storage.

        if not os.path.exists(pw_path):
            # Stores the password hash if it doesn't already exist.
            with open(pw_path, "w") as w:
                w.write(pw_gen)
        else:
            # Replaces the existing password hash if it already exists.
            with open(pw_path, "w") as w:
                w.write(pw_gen)

        encrypt_zip(zip_filename, files)
        # Calls the `encrypt_zip` function to encrypt the specified files.
        click.secho("Encrypted zip folder created successfully: {}".\
                    format(zip_filename), fg="red")
    elif command == "decrypt":
        # If the "decrypt" command is selected:

        with open(pw_path, "r") as r:
            pw_gen = r.readlines()[0]
            # Reads the stored password hash.

            if check_password_hash(pw_gen, pw.lower()):
                # Verifies the user-provided password against the stored hash.
                decrypted_files = decrypt_zip(zip_filename)
                # Calls the `decrypt_zip` function to decrypt the ZIP file.

                if decrypted_files is not None:
                    click.secho("Zip folder decrypted successfully.", fg="blue")
                    click.secho("Decrypted files: ", fg="yellow")
                    for file in decrypted_files:
                        click.secho(file, fg="green")
            else:
                click.secho("Invalid password", fg="red")
                # Displays an error if the password is invalid.

    else:
        click.secho("Invalid input: Must be either create or decrypt", fg="red")
        # Handles invalid command inputs.

def encrypt_zip(zip_filename, files):
    # Function to encrypt files into a ZIP archive.

    fernet_key = Fernet.generate_key()
    # Generates a unique encryption key.
    cipher_suite = Fernet(fernet_key)
    # Creates a Fernet cipher object for encryption.

    sub_folder = "enc_" + dt.now().strftime("%Y_%m_%d_%H_%M_%S")
    full_path = folder + os.sep + sub_folder
    os.mkdir(full_path)
    # Creates a timestamped subfolder for the encrypted ZIP file and key.

    with zipfile.ZipFile(full_path + os.sep + zip_filename, "w",
                         zipfile.ZIP_DEFLATED) as z:
        for file in files:
            z.write(file, os.path.basename(file))
            # Adds each specified file to the ZIP archive.

    with open(full_path + os.sep + "key.key", "wb") as key_file:
        key_file.write(fernet_key)
        # Stores the encryption key in the subfolder.

    with open(full_path + os.sep + zip_filename, "rb+") as z:
        encrypted_data = cipher_suite.encrypt(z.read())
        # Encrypts the contents of the ZIP file.
        z.seek(0)
        z.write(encrypted_data)
        # Writes the encrypted data back into the file.

def list_all():
    # Function to list all folders in the `ENC` directory.

    folders = os.listdir(folder)
    for f in range(len(folders)):
        if folders[f].startswith("enc_"):
            print(f, folders[f])
            # Prints folders starting with "enc_".

    return folders 

def decrypt_zip(zip_filename):
    # Function to decrypt a ZIP file.

    folders = list_all()
    zf = input("Pick a zipfile to decrypt:")

    folder_index_list = [str(folders.index(i)) for i in folders
                         if i.startswith("enc_")]
    # Filters folders starting with "enc_".

    if zf in folder_index_list:
        zf_int = int(zf)
    else:
        print("Invalid input: Must be an integer")
        return None

    sub_folder = folders[zf_int]
    full_path = folder + os.sep + sub_folder

    with open(full_path + os.sep + "key.key", "rb") as key_file:
        fernet_key = key_file.read()
        # Reads the encryption key.

    cipher_suite = Fernet(fernet_key)

    with open(full_path + os.sep + zip_filename, "rb") as z:
        decrypted_data = cipher_suite.decrypt(z.read())
        # Decrypts the ZIP file contents.

    with open(full_path + os.sep + zip_filename, "wb") as z:
        z.write(decrypted_data)
        # Writes the decrypted data back to the file.

    decrypted_files = []
    with zipfile.ZipFile(full_path + os.sep + zip_filename, "r") as z:
        namelist = z.namelist()
        for file in namelist:
            z.extract(file)
            decrypted_files.append(file)
            # Extracts each file and adds its name to the list.

    enc_name = folder + os.sep + sub_folder
    dec_name = folder + os.sep + sub_folder.replace("enc", "dec")
    os.rename(enc_name, dec_name)
    # Renames the folder to indicate it is decrypted.

    return decrypted_files

if __name__ == "__main__":
    cli()
    # Runs the CLI application when the script is executed directly.
