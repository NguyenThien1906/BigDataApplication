import redis
import pandas as pd
import gc
import json

json_input_file = "db_config.json"
config_json = json.load(open(json_input_file, 'r'))

# Kết nối tới Redis
redis_host = config_json['redis_host']  # Địa chỉ IP của Ubuntu
redis_port = config_json['redis_port']  # Cổng Redis mặc định

r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# ---------------------- #
#  LƯU THÔNG TIN ANIME   #
# ---------------------- #
def read_anime_dataset(fname):
    print("Đang đọc file anime-dataset-2023.csv ...")
    chunk_size = 50000  # Đọc file theo từng phần nhỏ
    for chunk in pd.read_csv(fname, chunksize=chunk_size):
        data = chunk.to_dict(orient="records")  # Tăng tốc so với iterrows()

        for row in data:
            # Lưu thông tin Anime vào Redis dưới dạng Hash với Key là anime_id
            anime_id = row["anime_id"]
            r.hset(f"anime:{anime_id}", mapping=row)

    print("Hoàn thành lưu thông tin anime vào Redis!")
    del chunk, data
    # Giải phóng bộ nhớ
    gc.collect()


# -------------------------------   #
#  LƯU THÔNG TIN CÁ NHÂN NGƯỜI DÙNG #
# -------------------------------   #
def read_users_details(fname):
    print("Đang đọc file users-details-2023.csv ...")
    chunk_size = 50000
    for chunk in pd.read_csv(fname, chunksize=chunk_size):
        data = chunk.to_dict(orient="records")

        for row in data:
            # Lưu thông tin cá nhân người dùng vào Redis dưới dạng Hash với Key là user_id
            user_id = row["Mal ID"]
            r.hset(f"user:{user_id}", mapping=row)

    print("Hoàn thành lưu thông tin người dùng vào Redis!")
    del chunk, data
    # Giải phóng bộ nhớ
    gc.collect()


# ------------------------------ #
#  LƯU ĐIỂM ĐÁNH GIÁ NGƯỜI DÙNG  #
# ------------------------------ #
def read_users_rating(fname):
    print("Đang đọc file users-score-2023.csv ...")
    chunk_size = 100000  # Đọc 100,000 dòng mỗi lần để tăng tốc
    for chunk in pd.read_csv(fname, chunksize=chunk_size):
        #    chunk = chunk.fillna("")  # Xử lý NaN
        data = chunk.to_dict(orient="records")

        for row in data:
            user_id = row["user_id"]
            anime_id = row["anime_id"]
            rating = row["rating"]
            # Lưu giá trị rating dưới dạng String trong Redis với Key là {user_id}_{anime_id}
            r.set(f"{user_id}_{anime_id}", rating)

    print("Hoàn thành lưu điểm đánh giá vào Redis!")
    del chunk, data
    # Giải phóng bộ nhớ
    gc.collect()
    print("Dữ liệu đã được lưu vào Redis thành công!")


if __name__ == "__main__":

    fname_anime = config_json['anime_details']
    fname_details = config_json['user_details']
    fname_rating = config_json['anime_ratings']

    # Đọc file csv chứa danh sách thông tin anime
    read_anime_dataset(fname_anime)
    # Đọc file csv chứa thông tin của các user
    #read_users_details(fname_details)
    # Đọc file csv chứa danh sách đánh giá các anime
    read_users_rating(fname_rating)
