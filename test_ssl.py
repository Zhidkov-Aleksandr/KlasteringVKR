import requests

url = "http://rosstat.gov.ru/storage/mediabank/3inf_MP_2024.xlsx"
try:
    print("Trying HTTP...")
    resp = requests.get(url, verify=False, timeout=10)
    print("HTTP Success:", resp.status_code)
except Exception as e:
    print("HTTP Error:", e)

url_https = "https://rosstat.gov.ru/storage/mediabank/3inf_MP_2024.xlsx"
try:
    print("Trying HTTPS without verify...")
    resp = requests.get(url_https, verify=False, timeout=10)
    print("HTTPS Success:", resp.status_code)
except Exception as e:
    print("HTTPS Error:", e)
