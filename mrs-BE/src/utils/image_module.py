import os

from ..settings.path import *

def create_upload_directory(dir_name="images/"):
    os.makedirs(dir_name, exist_ok=True)  

def delete_files_in_directory(dir_path = IMG_PATH):
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            
def initialize_upload_directory():
    create_upload_directory()
    delete_files_in_directory(IMG_PATH)

def save_images_to_directory(images="images", dir_name="images/"):
    
    existing_files = len([f for f in os.listdir(dir_name) if f.startswith("image_")])
    saved_paths = [] # 저장된 경로를 담을 리스트 추가
    
    for i, image in enumerate(images, 1):
            # 0. 파일확장자 추출 및 고유 파일명 생성
            _, file_extension = os.path.splitext(image.filename)
            unique_filename = f"image_{existing_files + i}{file_extension}"
            file_path = os.path.join(dir_name, unique_filename)
            
            # 1. 파일 읽기 (FastAPI의 SpooledTemporaryFile 대응)
            contents = image.file.read() 
            print(f"[{unique_filename}] 수신 크기: {len(contents)} bytes")  # 추가
            
            # 2. 파일 저장 (읽어둔 contents 사용으로 수정)
            with open(file_path, "wb") as f:
                f.write(contents)
            #saved_paths.append(file_path)

            # 3. 검증 로그 출력
            saved_size = os.path.getsize(file_path)
            print(f"[{unique_filename}] 저장 크기: {saved_size} bytes")
            
            # <- 저장된 파일의 '절대 경로'를 리스트에 추가
            # 절대 경로를 사용해야 다른 폴더(services 등)에서 파일을 찾을 때 에러가 안 납니다.
            saved_paths.append(os.path.abspath(file_path))
            # saved_size = os.path.getsize(file_path) # 추가
            # print(f"[{unique_filename}] 저장 크기: {saved_size} bytes") # 추가
    
    # 5. 최종 경로 리스트 반환
    return saved_paths
            
            
                
def to_list():
    img_list = os.listdir(IMG_PATH)
    full_img_list = [IMG_PATH + "/" + image for image in img_list]
    return full_img_list