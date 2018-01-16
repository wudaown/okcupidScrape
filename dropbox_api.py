import dropbox
class Dropbox_API:
    def __init__(self, access_token):
        self.ACCESS_TOKEN = access_token
        self.dbx = dropbox.Dropbox(self.ACCESS_TOKEN)

    def upload_file(self,localpath, remotepath):
        try:
            print('Uploading %s to %s' % (localpath, remotepath))
            with open(localpath,'rb') as f:
                self.dbx.files_upload(f.read(), remotepath, mute=True)
        except Exception as err:
            print(" - Failed to upload %s\n%s" % (localpath, err))
            return False

        print(" - Finished upload.")
        return True

    def list_dir(self, path):
        filenames = []
        for entry in self.dbx.files_list_folder(path).entries:
            filenames.append(entry.name)
        return filenames

    def download_file(self, download_path, local_path=None):
        try:
            if local_path is None:
                self.dbx.files_download_to_file(download_path.split('/')[-1], download_path)
            else:
                self.dbx.files_download_to_file(local_path, download_path)
            return True
        except dropbox.exceptions.ApiError:
            print('\t[Error] Error in downloading...')
            return False