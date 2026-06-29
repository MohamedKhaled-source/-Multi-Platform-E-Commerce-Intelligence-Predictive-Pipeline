import requests
from bs4 import BeautifulSoup
import pandas as pd
data = []
for page in range(1, 7):  
    URL = f"https://www.elarabygroup.com/en/tvs-and-electronics/televisions/smart-tvs?page={page}"
    r = requests.get(URL)
    soup = BeautifulSoup(r.content, "html.parser")
    
    products = soup.find_all("div", class_="product-item-info")
   
    for p in products:
      brand = type_ = size = resolution = warranty = "Nan"
      try:
        title = p.find("a", class_="product-item-link").text.strip()
      except :
        title ="Nan"
      try:
        link = p.find("a", class_="product-item-link").get("href")
      except:
        link = "Nan"
      try:
        price = p.find("span",class_="price").text.strip()
      except:
        price = "Nan"
      try:
        rate=p.find("span",class_="my-rating-badge__value").text.strip()
      except:
        rate = "Nan"
      if link:
        try:
          prod_r = requests.get(link)
          soup_product = BeautifulSoup(prod_r.content , "html5lib")

          specs = {}
          spec_table = soup_product.find(id="product-attribute-specs-table")

          spec_rows = spec_table.find_all("tr")
          for row in spec_rows:
              th = row.find("th")
              td = row.find("td")
              if th and td:
                  specs[th.get_text(strip=True)] = td.get_text(strip=True)

          brand = specs.get("Brand")
          type_ = specs.get("Type")
          size = specs.get("Size")
          resolution = specs.get("Resolution")
          warranty = specs.get("Warranty")
        
        except Exception:
          print(f"Could not load details for {title} ")
      
      data.append({
            "Title": title,
            "Link": link,
            "Price": price,
            "Rate": rate,
            "Brand": brand,
            "Type": type_,
            "Size": size,
            "Resolution": resolution,
            "Warranty": warranty
        })
        
df = pd.DataFrame(data)
df.to_csv("by_request_way1.csv",index = False)



