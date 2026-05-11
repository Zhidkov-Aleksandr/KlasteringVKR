import requests
url = "https://rosstat.gov.ru/storage/mediabank/3inf_MP_2024.xlsx"
try:
    resp = requests.get(url, verify=False, timeout=20)
    print("Downloaded:", len(resp.content), "bytes")
except Exception as e:
    print("Download error:", e)
