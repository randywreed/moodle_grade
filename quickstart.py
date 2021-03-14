from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
gauth = GoogleAuth()
gauth.LoadCredentialsFile("grade_reflections_cred.txt")
drive = GoogleDrive(gauth)
file=drive.CreateFile({'title':"Rel_1010_Spring_2021_Religion and Religious Studies Lecture Reflection01-22-2021grades.csv",'parents':[{'id':'1aTZ4UpN9geNXma_hWNwk5Qyx9HXxiIfn'}]})
file.Upload()

file_list = drive.ListFile({'q': '"1aTZ4UpN9geNXma_hWNwk5Qyx9HXxiIfn" in parents and trashed=false'}).GetList()

for file in file_list:
    print(file['title'], file['id'])