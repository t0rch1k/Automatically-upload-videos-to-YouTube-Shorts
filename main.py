from os import getenv, path, listdir
import json
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()


def find_credentials_file():
    script_dir = path.dirname(path.abspath(__file__))
    for file in listdir(script_dir):
        if file.endswith('.json'):
            file_path = path.join(script_dir, file)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if 'installed' in data or 'web' in data:
                        print(f"Найден файл с учетными данными: {file_path}")
                        return file_path
            except json.JSONDecodeError:
                continue
    raise FileNotFoundError('Не найден JSON файл с учетными данными OAuth в директории скрипта')


CLIENT_SECRETS_FILE = find_credentials_file()
VIDEOS_FOLDER = getenv('VIDEOS_FOLDER', 'videos')


class YouTubeShortsUploader:
    def __init__(self, client_secrets_file, videos_folder):
        self.videos_folder = videos_folder
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]

        # Добавляем open_browser=True для автоматического открытия браузера
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, self.scopes)
        print("Ожидание авторизации через браузер...")
        credentials = flow.run_local_server(port=0, open_browser=True)
        print("Авторизация прошла успешно!")

        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=credentials)

    def get_video_details(self, video_path):
        title = path.splitext(path.basename(video_path))[0]
        description = "Uploaded"
        return title, description

    def upload_short(self, video_path):
        try:
            title, description = self.get_video_details(video_path)
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'categoryId': '22'
                },
                'status': {
                    'privacyStatus': 'public'
                }
            }

            media = MediaFileUpload(
                video_path,
                resumable=True,
                chunksize=1024 * 1024
            )

            request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )

            response = request.execute()

            print(f"Видео {title} успешно загружено. ID: https://www.youtube.com/shorts/{response['id']}")
            return response['id']

        except googleapiclient.errors.HttpError as e:
            print(f"Ошибка при загрузке видео {video_path}: {e}")
            return None
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            return None

    def upload_all_shorts(self):
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv']
        video_files = [f for f in listdir(self.videos_folder) if
                       any(f.lower().endswith(ext) for ext in video_extensions)]

        if not video_files:
            print("В папке с видео не найдено файлов для загрузки.")
            return

        print(f"Найдено видео файлов: {len(video_files)}")

        for filename in video_files:
            video_path = path.join(self.videos_folder, filename)
            print(f"Загрузка видео: {filename}")
            self.upload_short(video_path)


def main():
    print("Запуск загрузчика YouTube Shorts...")
    uploader = YouTubeShortsUploader(CLIENT_SECRETS_FILE, VIDEOS_FOLDER)
    uploader.upload_all_shorts()

if __name__ == "__main__":
    main()