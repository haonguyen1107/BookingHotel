from datetime import datetime, timedelta
from help_function.crawl_func import *
from help_function.query_db import *
from airflow import DAG 
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import pandas as pd
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.models import Variable
import os
class ETL():
    def __init__(self):
        self.name_raw_table = 'BookingHotel'
    def get_config(self):
        config = Variable.get("config", deserialize_json = True)
        print(config)
        return config
    def extract_data(self, config,**kwargs):
        config_db = config['config_db']
        conn = MySqlHook(mysql_conn_id = config_db['database']).get_conn()
        checkin, checkout, weekday = get_date(conn)
        booking_links = config['booking_links']
        data = get_today_dataframe(checkin, checkout, weekday,booking_links)
        name_file_excel = 'data.xlsx'
        data.to_excel(name_file_excel,index =False)
        ti = kwargs['ti']
        ti.xcom_push(key = 'name_file_excel', value =name_file_excel)

    def transform_data(self, **kwargs):
        ti = kwargs['ti']
        path_excel = ti.xcom_pull(task_ids = 'crawl_data',key = 'name_file_excel')
        data = pd.read_excel(path_excel)
        os.remove(path_excel)
        data = clean_data(data)
        name_file_excel_clean = 'data_clean.xlsx'
        data.to_excel(name_file_excel_clean,index =False)
        ti = kwargs['ti']
        ti.xcom_push(key = 'name_file_excel_clean', value =name_file_excel_clean)

    def load(self,**kwargs):
        ti = kwargs['ti']
        path_excel = ti.xcom_pull(task_ids = 'transform_data',key = 'name_file_excel_clean')
        data = pd.read_excel(path_excel)
        os.remove(path_excel)
        config = Variable.get("config", deserialize_json = True)
        config_db = config['config_db']
        conn = MySqlHook(mysql_conn_id = config_db['database']).get_conn()
        insert_db(data,conn,self.name_raw_table)
    def no_data(self):
        print(f"have no data today")
    

# {
#     "config_db":{
#         "user" : "sltadm",
#         "password" : "password123",
#         "host": "host.docker.internal",
#         "port" : "3306",
#         "database" : "Booking"

#     },

#     "booking_links":
#         {
#          "Hồ Chí Minh": "https://www.booking.com/searchresults.vi.html?ss=TP.+H%C3%B4%CC%80+Chi%CC%81+Minh%2C+Vi%C3%AA%CC%A3t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAL1lMaoBsACAdICJGM1MWM1ODQyLWYzMmMtNGExMi1iMWFmLWM4YzliMDE0MzJlMNgCBeACAQ&sid=a3cf4761bc87283185953cebac7c42a2&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=-3730078&dest_type=city&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Hà Nội": "https://www.booking.com/searchresults.vi.html?ss=Ha%CC%80+N%C3%B4%CC%A3i%2C+Vi%C3%AA%CC%A3t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALDmMaoBsACAdICJDk4YmE4ZjY1LTY2YWMtNDM1YS05NGEzLWYxMTE4MDA5MmMzNNgCBeACAQ&sid=3fad67540608476afb06c23007af9769&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=-3714993&dest_type=city&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Kiên Giang": "https://www.booking.com/searchresults.vi.html?ss=Ki%C3%AAn+Giang%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKGmcaoBsACAdICJGQ5MDFiYTI1LTBiMDQtNDE4My1iMzUwLWI1MmY3MDA1N2ViMtgCBeACAQ&sid=09a51afba63e2d8ac1241ffd81ab8919&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=5405&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=c6f75f83edcf016d&ac_meta=GhBjNmY3NWY4M2VkY2YwMTZkIAAoATICdmk6C0tpw6puIEdpYW5nQABKAFAA&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "An Giang": "https://www.booking.com/searchresults.vi.html?ss=An+Giang%2C+Vietnam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALMmcaoBsACAdICJDY5MjcxZTdhLTMwNWYtNDM3OC1iMzg5LTY2MmFmNzdjNWQ0Y9gCBeACAQ&sid=ab77dcbfb006fe3f7fdfe74decca51b8&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6891&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=en&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=a60e5fa661ca0190&ac_meta=GhBhNjBlNWZhNjYxY2EwMTkwIAAoATICZW46CEFuIEdpYW5nQABKAFAA&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Bình Thuận": "https://www.booking.com/searchresults.vi.html?ss=B%C3%ACnh+Thu%E1%BA%ADn%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKNmsaoBsACAdICJDBjOTVkNDIyLTYyODMtNDk4Mi1iMTc1LTlhOGU1NjdlY2UxY9gCBeACAQ&sid=87a6742fbac4e5848ef6524ebe6a5eb0&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=5391&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=b7345fc63e51009f&ac_meta=GhBiNzM0NWZjNjNlNTEwMDlmIAAoATICdmk6DULDrG5oIFRodeG6rW5AAEoAUAA%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Khánh Hòa":"https://www.booking.com/searchresults.vi.html?ss=Kh%C3%A1nh+H%C3%B2a%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALSmsaoBsACAdICJDEzNGM1YzQ5LTMyODctNGMzYi1hYTE1LTU2ZjA4YmU2YTZlN9gCBeACAQ&sid=714f03f9d5e7d659498d52c3efeb1a55&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=5425&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=906e5fe9d6370663&ac_meta=GhA5MDZlNWZlOWQ2MzcwNjYzIAAoATICdmk6C0tow6FuaCBIw7JhQABKAFAA&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Đà Nẵng": "https://www.booking.com/searchresults.vi.html?ss=Th%C3%A0nh+ph%E1%BB%91+%C4%90%C3%A0+N%E1%BA%B5ng%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALppcaoBsACAdICJGZjMzM5YTI4LTBjZTAtNGE1MS04ZmQxLTQxYTk4MDg3MGUzYtgCBeACAQ&sid=94021cd962e0a96f854086cc6be18575&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6232&dest_type=region&ac_position=1&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=7c9c62b4b1aa0237&ac_meta=GhA3YzljNjJiNGIxYWEwMjM3IAEoATICdmk6C8SQw6AgTuG6tW5nQABKAFAA&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Hải Phòng": "https://www.booking.com/searchresults.vi.html?ss=H%E1%BA%A3i+Ph%C3%B2ng%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKnpsaoBsACAdICJGNiMzJhYjg1LTVkZGItNGNlMC1hNTM5LTViYzVhZjA2YzYzMNgCBeACAQ&sid=e89cd9f5cf55e144ef4bff020db2eb35&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6266&dest_type=region&ac_position=1&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=68ab62d3f6220088&ac_meta=GhA2OGFiNjJkM2Y2MjIwMDg4IAEoATICdmk6DEjhuqNpIFBow7JuZ0AASgBQAA%3D%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Quảng Ninh": "https://www.booking.com/searchresults.vi.html?ss=Qu%E1%BA%A3ng+Ninh%2C+Qu%E1%BA%A3ng+Ninh%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALhpsaoBsACAdICJDFjNGNhMzhhLWFiYjEtNGU3OS1iOGI2LTk5OWM5NmQzZmRiY9gCBeACAQ&sid=305242b05757b522990c5bf809238988&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=-3727317&dest_type=city&ac_position=1&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=7c9c62f1c98d012f&ac_meta=GhA3YzljNjJmMWM5OGQwMTJmIAEoATICdmk6DFF14bqjbmcgTmluaEAASgBQAA%3D%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Lâm Đồng": "https://www.booking.com/searchresults.vi.html?ss=L%C3%A2m+%C4%90%E1%BB%93ng%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAK2qMaoBsACAdICJDcxOTRkNWNmLTk4NTctNDU3Ny04YmI3LTMxZmJjOTJhOWFhNtgCBeACAQ&sid=aa3392079283a43e7fc94bc100050e67&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6269&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=8174635b800e0029&ac_meta=GhA4MTc0NjM1YjgwMGUwMDI5IAAoATICdmk6DEzDom0gxJDhu5NuZ0AASgBQAA%3D%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Lào Cai": "https://www.booking.com/searchresults.vi.html?ss=L%C3%A0o+Cai%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKZq8aoBsACAdICJDAzYmNjMzNlLTA2YjMtNGUyNy1iMmMxLTY3YTAzOTRhNzE4ONgCBeACAQ&sid=0e97ea67898fd629a76ded035e807664&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6265&dest_type=region&ac_position=2&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=4d2e640c75a9008a&ac_meta=GhA0ZDJlNjQwYzc1YTkwMDhhIAIoATICdmk6CEzDoG8gQ2FpQABKAFAA&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Thái Bình": "https://www.booking.com/searchresults.vi.html?ss=Th%C3%A1i+B%C3%ACnh%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALCq8aoBsACAdICJDJmZDU3YzYxLWFiMzEtNDhlZS04Y2UwLTY1ZDQ1YmU5MjRhOdgCBeACAQ&sid=81f056d0bd759f06f84910f3e86395c6&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6866&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=2c686421e2a1006a&ac_meta=GhAyYzY4NjQyMWUyYTEwMDZhIAAoATICdmk6C1Row6FpIELDrG5oQABKAFAA&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Cần Thơ": "https://www.booking.com/searchresults.vi.html?ss=C%E1%BA%A7n+Th%C6%A1%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALXrcaoBsACAdICJGU5ZmJkMTdjLWFlNTctNGM3OC1hMjI1LWZiMmMzMDM0YThjM9gCBeACAQ&sid=10ef59ac4ef8cf2c8b0aa90aa40f83f7&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6230&dest_type=region&ac_position=2&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=6dc964ac81800328&ac_meta=GhA2ZGM5NjRhYzgxODAwMzI4IAIoATICdmk6CkPhuqduIFRoxqFAAEoAUAA%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Quảng Bình": "https://www.booking.com/searchresults.vi.html?ss=Qu%E1%BA%A3ng+B%C3%ACnh%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAL7rcaoBsACAdICJDdjMmIxYTZlLWUwM2UtNDBmNi1hNzU1LTRlMzA3NTM1OTA1MNgCBeACAQ&sid=8c5757c746997dbe16e3bfd227eb8e12&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6927&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=8b1e64bd75e80354&ac_meta=GhA4YjFlNjRiZDc1ZTgwMzU0IAAoATICdmk6DVF14bqjbmcgQsOsbmhAAEoAUAA%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Huế": "https://www.booking.com/searchresults.vi.html?ss=Hu%E1%BA%BF%2C+Th%E1%BB%ABa+Thi%C3%AAn+-+Hu%E1%BA%BF%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKhrsaoBsACAdICJDUzNzI4NGRjLWUyNTQtNGZlMi04ZDNmLWNhNjllZDUxNmQ1MNgCBeACAQ&sid=4090bea462b4e98000bf70fd862083ed&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=-3715887&dest_type=city&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=63b464d071050146&ac_meta=GhA2M2I0NjRkMDcxMDUwMTQ2IAAoATICdmk6BUh14bq%2FQABKAFAA&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Cao Bằng":"https://www.booking.com/searchresults.vi.html?ss=Cao+Bang%2C+Vietnam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALorsaoBsACAdICJDkwYjE2ODZkLTFhMjgtNGQwZC1hZmM0LTg4OGI0ODQ1NDA1MNgCBeACAQ&sid=d60ac00b941052ab31195f448c574785&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6907&dest_type=region&ac_position=1&ac_click_type=b&ac_langcode=en&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=2b9b64f40cf101f5&ac_meta=GhAyYjliNjRmNDBjZjEwMWY1IAEoATICZW46E0NhbyBC4bqxbmcsIFZpZXRuYW1AAEoAUAA%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Đắk Lắk": "https://www.booking.com/searchresults.vi.html?ss=%C4%90%E1%BA%AFc+L%E1%BA%AFc%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALcr8aoBsACAdICJDAxY2E0OTE2LWY1YzEtNDYwNy1hYmFkLWM4NzFhYzljZDI1MdgCBeACAQ&sid=4032dd64e9bbfc4448aef5b321fe894d&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6880&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=3&search_selected=true&search_pageview_id=4ee0652e32d20100&ac_meta=GhA0ZWUwNjUyZTMyZDIwMTAwIAAoATICdmk6DMSQ4bqvYyBM4bqvY0AASgBQAA%3D%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Bà Rịa - Vũng Tàu": "https://www.booking.com/searchresults.vi.html?ss=B%C3%A0+R%E1%BB%8Ba+-+V%C5%A9ng+T%C3%A0u%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKysMaoBsACAdICJDMzZjgzMmI0LWQ2OWItNGQ3NC05YjVlLTE3YmUxMjVkYjlkZNgCBeACAQ&sid=50edefab3f9ea3225b144fc3b87a3154&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6233&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=68056559f39a02be&ac_meta=GhA2ODA1NjU1OWYzOWEwMmJlIAAoATICdmk6DELDoCBS4buLYSAtIEAASgBQAA%3D%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Phú Yên": "https://www.booking.com/searchresults.vi.html?ss=Ph%C3%BA+Y%C3%AAn%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALZsMaoBsACAdICJDgyM2IzMmY4LTBhNzMtNGYwYi05NGVjLTE0ZGU0N2RkNmQ2M9gCBeACAQ&sid=fcd380199bfe92ccd46a326a6360d068&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6268&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=9fa4656c552203cf&ac_meta=GhA5ZmE0NjU2YzU1MjIwM2NmIAAoATICdmk6CVBow7ogWcOqbkAASgBQAA%3D%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Bình Định": "https://www.booking.com/searchresults.vi.html?ss=B%C3%ACnh+%C4%90%E1%BB%8Bnh%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKGscaoBsACAdICJGE2ODFiMDViLWNiZDItNDMxMC1hMGEwLTI2ZWQ1ZDA5MzEzZNgCBeACAQ&sid=7865e80476f9bb5f4ba3c2ea00ce7452&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6923&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=551f6583546500d8&ac_meta=GhA1NTFmNjU4MzU0NjUwMGQ4IAAoATICdmk6DULDrG5oIMSQ4buLbmhAAEoAUAA%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Đồng Tháp": "https://www.booking.com/searchresults.vi.html?ss=%C4%90%E1%BB%93ng+Th%C3%A1p%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKwscaoBsACAdICJGJkN2FmOWFiLWI2ZTgtNGVhZC05NmJkLWIwZmM5YTdmOTkwOdgCBeACAQ&sid=4255dce1f5a270f29ec9a577a5cb49ad&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6890&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=e651659869b100b4&ac_meta=GhBlNjUxNjU5ODY5YjEwMGI0IAAoATICdmk6DcSQ4buTbmcgVGjDoXBAAEoAUAA%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Cà Mau": "https://www.booking.com/searchresults.vi.html?ss=C%C3%A0+Mau%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALRs8aoBsACAdICJGM4MDA5ODI2LWMwYTgtNDg1NC1iZDhmLTFhMTAxYTlkYzYzNtgCBeACAQ&sid=bd80f726d8685b5b06d34022f2ecec74&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6895&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=795266281f340245&ac_meta=GhA3OTUyNjYyODFmMzQwMjQ1IAAoATICdmk6B0PDoCBNYXVAAEoAUAA%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Quảng Ngãi": "https://www.booking.com/searchresults.vi.html?ss=Qu%E1%BA%A3ng+Ng%C3%A3i%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKSk8qoBsACAdICJGY3ZjFmZGUyLWYyMmQtNGUyNi05ZTJkLTcwOTZlMGUyYmJkMNgCBeACAQ&sid=b241ab415eb56bb80f6e41ed3482e600&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6924&dest_type=region&ac_position=1&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=6a7f3549848000f8&ac_meta=GhA2YTdmMzU0OTg0ODAwMGY4IAEoATICdmk6DVF14bqjbmcgTmfDo2lAAEoAUAA%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Ninh Bình": "https://www.booking.com/searchresults.vi.html?ss=Ninh+B%C3%ACnh%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuALntMaoBsACAdICJDgwZTlmNDFkLTMxNmEtNGJiMC1hZGM3LTgwN2Y1MzM4MGQyNtgCBeACAQ&sid=8fc07233268296c280aa4c70ee9566b1&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6267&dest_type=region&ac_position=2&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=46456673a6bd01ff&ac_meta=GhA0NjQ1NjY3M2E2YmQwMWZmIAIoATICdmk6Ck5pbmggQsOsbmhAAEoAUAA%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0",
#         "Tây Ninh": "https://www.booking.com/searchresults.vi.html?ss=T%C3%A2y+Ninh%2C+Vi%E1%BB%87t+Nam&efdco=1&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKVtcaoBsACAdICJDgyYTIzYzgxLWU5NmQtNDVhNy1iYTljLWI2NjI1MjQ1NGUyMNgCBeACAQ&sid=5a0b15c965d57334ad387f8f4a9eabdb&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=6883&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=7b3d668a3b5b0212&ac_meta=GhA3YjNkNjY4YTNiNWIwMjEyIAAoATICdmk6CVTDonkgTmluaEAASgBQAA%3D%3D&checkin={checkin}&checkout={checkout}&group_adults={adult}&no_rooms={room}&group_children={children}&sb_travel_purpose=leisure&selected_currency={currency}&offset=0"
#     }

# }