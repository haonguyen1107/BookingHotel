import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import datetime as dt # Thư viện để xử lý timestamp
import pytz # Thử viện để đổi timezone
from datetime import timezone, timedelta, datetime
import mysql.connector
import  numpy as np 
def get_today_date():
  """
  Hàm để tự động lấy ra ngày hôm nay và ngày mai cũng như weekday của hôm nay.
  Tính theo timezone của Việt Nam (UTC+7)
  Input: Nothing
  Output:
    - checkin (string): Ngày hôm nay. Format "%Y-%m-%d"
    - checkout (string): Ngày mai. Format "%Y-%m-%d"
    - weekday (string): Thứ trong tuần (Monday, Tuesday, Wednesday,..., Sunday)
  """
  # Define the Vietnam Standard Time (UTC+7) timezone
  vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')

  # Lấy date và của today
  today = dt.datetime.now(vietnam_timezone).date()
  print('vietnam_timezone',vietnam_timezone, today)

  # Lấy phần date tomorrow
  tomorrow = today + dt.timedelta(days = 1)

  # Lấy weekday
  weekday = today.strftime('%A')

  # Convert sang string để làm thành checkin và checkout:
  checkin = today.strftime("%Y-%m-%d")
  checkout = tomorrow.strftime("%Y-%m-%d")

  return checkin, checkout, weekday


def get_date(conn):
    """
    Input: config db
    Output:
    - checkin (string): Ngày hôm nay. Format "%Y-%m-%d"
    - checkout (string): Ngày mai. Format "%Y-%m-%d"
    - weekday (string): Thứ trong tuần (Monday, Tuesday, Wednesday,..., Sunday)
    """
    
    # conn = mysql.connector.connect(user = config['user'],
    #                            host = config['host'],
    #                            password = config['password'],
    #                           database = config['database'])

    
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(Checkout) FROM BookingHotel")
    max_date = cursor.fetchall()
    cursor.close()
    conn.close()
    
    try:
      max_date = str(max_date[0][0])
      if(max_date!='None'):
        check_in = datetime.strptime(max_date,'%Y-%m-%d')
        n = timedelta(days=1)
        weekday = check_in.strftime('%A')
        check_out = (check_in+n).strftime('%Y-%m-%d')
        check_in = check_in.strftime('%Y-%m-%d')
      else:
        check_in, check_out, weekday = get_today_date()
    except: 
      check_in, check_out, weekday = get_today_date()
    return check_in, check_out, weekday
    

def crawl_booking_data(link, checkin, checkout, adult, room, children, currency):
  """
  Hàm để crawl các data khách sạn ở 1 tỉnh thành trên trang Booking.com
  Input:
    - link (string): Đường link trang Booking của tỉnh mình muốn crawl
    - checkin (string): Ngày checkin
    - checkout (string): Ngày checkout
    - adult (int): Số người lớn đi du lịch
    - room (int): Số phòng muốn đặt
    - children (int): Số trẻ em
    - currency (string): Đơn vị tiền tệ
  Output:
    - df (DataFrame): DataFrame chứa thông tin khách sạn của tỉnh đó trong 1 ngày.
  """
  adult = str(adult)
  room = str(room)
  children = str(children)
  link = link.replace('{checkin}', checkin).replace('{checkout}', checkout).replace('{adult}', adult).replace('{room}', room).replace('{children}', children).replace('{currency}', currency).replace('offset=0', 'offset={}')

  hotels = []

  for i in range(0, 40):
      print('link',link)
      url = link.format(i*25) # Increase by 25 cards

      headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"}

      response = requests.get(url, headers=headers)

      soup = BeautifulSoup(response.content, 'lxml')

      cards = soup.find_all('div', {'data-testid':'property-card'})

      for card in cards:
          title = card.find('div', {'data-testid':'title'}).get_text()

          location = card.find('span', {'data-testid':'address'}).get_text()

          room_type = card.find('span', {'class':'e8f7c070a7'})
          if room_type:
            room_type = room_type.get_text()
          else:
            room_type= "Not mentioned"

          score1 = card.find('div', {'class':'a3b8729ab1 d86cee9b25'})
          if score1:
              score = float(score1.get_text().replace(',', '.'))
          else:
              score = None

          rating1 = card.find('div', {'class':'a3b8729ab1 e6208ee469 cb2cbb3ccb'})
          if rating1:
              rating = rating1.get_text()
          else:
              rating = 'Not mentioned'

          review1 = card.find('div', {'class':'abf093bdfe f45d8e4c32 d935416c47'})
          if review1:
              review = str(review1.text.split(' ')[0])
          else:
              review = ''

          distance1 = card.find('span', {'data-testid':'distance'})
          if distance1:
              distance = distance1.get_text().replace(' from centre', '')
          else:
              distance = 'Not mentioned'

          price = card.find('span', {'data-testid':'price-and-discounted-price'})
          if price:
            price = float(price.get_text().split('\xa0')[1].replace('.', ''))
          else:
            price = None

          hotels.append([title, location, room_type, score, rating, review, distance, price])
  df = pd.DataFrame(hotels, columns=['Hotel Name', 'Location', 'Room Type', 'Score', 'Rating', 'Review', 'Distance From Centre', 'Price'])
  df.drop_duplicates(keep='first', inplace=True, ignore_index=True)
  return df

def get_today_dataframe(checkin, checkout, weekday,booking_links,adult = 2, room = 1, children = 0, currency="VND"):
  """
  Hàm để crawl data từ khách sạn của 25 tỉnh thành Việt Nam từ website Booking
  Input:
    - adult (int): Số người lớn. Mặc định = 2
    - room (int): Số lượng phòng. Mặc định = 1
    - children (int): Số trẻ em. Mặc định = 0
    - currency (string): Đơn vị tiền tệ cho Price. Mặc định là VND
  Output:
    - df (DataFrame): DataFrame hoàn chỉnh cho ngày hôm đó.
  """



  final_df = [] # Khởi tạo list chứa final DataFrame

  # Duyệt qua từng tỉnh thành
  for key in booking_links:
    province = key # Lấy tên tỉnh
    link = booking_links[key] # Lấy url

    # Crawl data về từ Booking
    df = crawl_booking_data(link, checkin, checkout, adult, room, children, currency)

    # Bổ sung các cột thông tin Checkin - Checkout - Weekday - Province
    df.insert(loc = 0, column='Checkin', value = checkin)
    df.insert(loc = 1, column='Checkout', value = checkout)
    df.insert(loc = 2, column='Weekday', value = weekday)
    df.insert(loc = 3, column='Province', value = province)

    # Append vào final_df chứa thông tin của các tỉnh
    final_df.append(df)
    # break

  # Chuyển final_df thành DataFrame hoàn chỉnh
  final_df = pd.concat(final_df)

  # Reset lại index
  final_df.reset_index(drop=True, inplace=True)

  return final_df


def extract_score(row):
  """
  Hàm dùng để tách những dòng có Rating mà bị dính cả score vào nữa và trả về 2 cột riêng
  """
  condition = re.search(r'(\d+(?:,\d+)?)$', row['Rating']) # Khớp digit cuối trong string
  if condition:
    row["Score"] = float(condition.group(1).replace(',', '.'))
    row["Rating"] = row["Rating"][:condition.start()] # Remove phần score
  return row

# def extract_distance(row):
#   """
#   Hàm dùng để xử lý Distance:
#    - Biến đổi Distance về dạng số (float)
#    - Những chỗ nào đơn vị là m thì quy đổi về km hết
#   """
#   condition = re.search(r'([\d,\.]+)', row["Distance From Centre"])
#   if condition:
#     # Tách phần số
#     numeric_part = condition.group(1)
#     # Đổi dấu , sang . và convert thành float
#     numeric_value = float(numeric_part.replace(',','.'))

#     temp = row["Distance From Centre"].replace('Cách trung tâm ', '').replace('km', '')
#     # Nếu đơn vị là m thì convert sang km
#     if 'm' in temp:
#       numeric_value /= 1000
#     return numeric_value
#   else:
#     return None
def extract_distance(distance):
  """
  Hàm dùng để xử lý Distance:
   - Biến đổi Distance về dạng số (float)
   - Những chỗ nào đơn vị là m thì quy đổi về km hết
  """
  condition = re.search(r'([\d,\.]+)', distance)
  if condition:
    # Tách phần số
    numeric_part = condition.group(1)
    # Đổi dấu , sang . và convert thành float
    numeric_value = float(numeric_part.replace(',','.'))

    temp = distance.replace('Cách trung tâm ', '').replace('km', '')
    # Nếu đơn vị là m thì convert sang km
    if 'm' in temp:
      numeric_value /= 1000
    return numeric_value
  else:
    return None
def clean_data(df, min_threshold = 150000):
  """
  Input: DataFrame
  Các giai đoạn xử lý:
  - Loại bỏ những dòng có giá trị Price < threshold (mặc định là 150.000)
  - Tách những dòng Rating lỗi thành Score - Rating. Đổi những chỗ có chữ "Điểm đánh giá" thành "Not mentioned"
  - Xử lý Distance From Centre
  - Convert type của cột Reviews thành int
  Output: Data đã được clean
  """
  # Bỏ Price < threshold
  df["Price"] = df["Price"].astype(float)
  df = df[df["Price"] > min_threshold]
  df = df.drop_duplicates(keep=False)
  df.reset_index(drop = True, inplace = True)
  if(len(df)):
    # Tách dòng Rating lỗi
    df = df.apply(extract_score, axis = 1)
    # Đổi chữ "Điểm đánh giá" thành "Not mentioned"
    df["Rating"].replace('Điểm đánh giá ', 'Not mentioned', inplace = True)

    # Xử lý Distance From Centre
    # df["Distance From Centre"] = df.apply(extract_distance, axis = 1)
    df["Distance From Centre"] = df.apply(lambda x: extract_distance(x['Distance From Centre']), axis=1)

    # Convert type của Review thành float
    df['Review'] = df['Review'].astype(str)
    df['Review'] = df['Review'].apply(lambda x: x.replace('.', '') if x is not None else x)
    df['Review'] = pd.to_numeric(df['Review'], errors='coerce')

  df.rename(columns = {'Distance From Centre':'DistanceFromCentre','Room Type':'RoomType','Hotel Name':'HotelName' }, inplace = True)
  return df