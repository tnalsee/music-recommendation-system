import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

IMG_PATH = os.path.join(ROOT_DIR, "images")
MODEL_PATH = os.path.join(ROOT_DIR, "src/ml/Vit_model_best_epoch_2.pth")
TAG_TABLE_PATH = os.path.join(ROOT_DIR,'csv/tag_table3.csv')
SONG_TABLE_PATH = os.path.join(ROOT_DIR,'csv/song_table3.csv')
IDX_JSON_PATH = os.path.join(ROOT_DIR,'src/services/class_idx_to_label.json')