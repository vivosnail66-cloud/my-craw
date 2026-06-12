from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import urllib.request
import datetime
import random
import time
import json
import csv
import os


with open('url.json', 'r') as f:
    WEB_PAGE_DICT = json.load(f)

START_PAGE = 1
PAGE_LOAD_TIME_MAX = 1
PAGE_LOAD_TIME_MIN = 1
TIMEOUT = 60
IMAGE_DIR = os.path.join(os.getcwd(), "Images")
OUTPUT_CSV = "output_%s.csv" % datetime.datetime.now().strftime("%Y-%m-%d")
ALL_PRODUCT_TXT = os.path.join(os.getcwd(), "all_products.txt")
ALL_PRODUCT_LINK = []
ALL_IMAGES = {}
HEADER = [
    "ID", "Type", "SKU", "Name", "Published", "Is featured?", "Visibility in catalog", "Short description",
    "Description", "Date sale price starts", "Date sale price ends", "Tax status", "Tax class", "In stock?", "Stock",
    "Backorders allowed?", "Sold individually?", "Weight (lbs)", "Length (in)", "Width (in)", "Height (in)",
    "Allow customer reviews?", "Purchase note", "Sale price", "Regular price", "Categories", "Tags", "Shipping class",
    "Images", "Download limit", "Download expiry days", "Parent", "Grouped products", "Upsells", "Cross-sells",
    "External URL", "Button text", "Position", "Woo Variation Gallery Images", "Attribute 1 name",
    "Attribute 1 value(s)", "Attribute 1 visible", "Attribute 1 global", "Attribute 2 name", "Attribute 2 value(s)",
    "Attribute 2 visible", "Attribute 2 global", "Meta: _wpcom_is_markdown", "Download 1 name", "Download 1 URL",
    "Download 2 name", "Download 2 URL"
]
BRAND_DICT = {
    "Louis Vuitton": "louis-vuitton",
    "Gucci": "gucci",
    "Chanel": "chanel",
    "Dior": "christian-dior",
    "Fendi": "fendi",
    "Prada": "prada",
    "Hermes": "hermes",
    "Celine": "celine",
    "Valentino": "valentino",
    "Chloe": "chloe",
    "Saint Laurent": "saint-laurent",
    "Goyard": "goyard",
    "Bottega Veneta": "bottega-veneta",
    "Jimmy Choo": "jimmy-choo",
    "Alexander Mcqueen": "alexander-mcqueen",
    "Miu Miu": "miu-miu",
    "Golden Goose": "golden-goose",
    "Balenciaga": "balenciaga",
    "Nike": "nike",
    "Adidas": "adidas",
    "Rolex": "rolex",
    "Cartier": "cartier",
}


def csvWriter(dataList, mode='a'):
    with open(OUTPUT_CSV, mode, newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        for data_dict in dataList:
            tempData = []
            for key in HEADER:
                tempData.append(data_dict[key])
            writer.writerow(tempData)


def updateProducts(url):
    with open(ALL_PRODUCT_TXT, 'a') as f:
        f.write(url + "\n")


def getExistingProducts():
    global ALL_PRODUCT_LINK

    with open(ALL_PRODUCT_TXT, 'r') as f:
        for line in f:
            if line.strip() != "":
                ALL_PRODUCT_LINK.append(line.strip())


def getExistingImages():
    global ALL_IMAGES

    for root, dirs, files in os.walk(IMAGE_DIR):
        for file in files:
            if file.lower().endswith('.jpg'):
                subCategory = root.split("\\")[-1]
                if subCategory not in ALL_IMAGES.keys():
                    ALL_IMAGES[subCategory] = []
                ALL_IMAGES[subCategory].append(file)


# def getDimension(short_desc):
#     width = height = depth = ""
#     for line in short_desc.split("\n"):
#         if "Size:" in line:
#             dimension_str = line.replace("Size:", "").strip()
#             if "W" in line and "H" in line and "D" in line:
#                 items = dimension_str.split("x")
#                 for item in items:
#                     if "W" in item:
#                         width = item.replace("W", "").strip()
#                     elif "H" in item:
#                         height = item.replace("H", "").strip()
#                     elif "D" in item:
#                         depth = item.replace("D", "").strip()
#                     else:
#                         raise Exception("Unexpected item found! %s from %s" % (item, line))
#             else:
#                 try:
#                     [width, height, depth] = dimension_str.split("x")
#                 except Exception:
#                     raise Exception("Error! %s" % line)
#             break
#
#     return width, height, depth

def getBrand(url):
    for brand, value in BRAND_DICT.items():
        if value in url:
            return brand
    return ""


def getDefaultImageLink(img_url):
    return img_url.replace("-small_default", "")


def downloadImages(driver, image_dir, subCategory):
    global ALL_IMAGES
    image_list = []

    images = driver.find_elements(by=By.CSS_SELECTOR, value="img[class='pro_gallery_thumb ']")
    for i in range(0, len(images)):
        while True:
            try:
                images = driver.find_elements(by=By.CSS_SELECTOR, value="img[class='pro_gallery_thumb ']")
                image_url = getDefaultImageLink(img_url=images[i].get_attribute("src"))
            except Exception:
                time.sleep(PAGE_LOAD_TIME_MIN)
                pass
            else:
                image_title = "_".join(image_url.split("/")[-2:])
                image_list.append("http://a.local/wp-content/uploads/" + image_title)
                if subCategory not in ALL_IMAGES.keys():
                    ALL_IMAGES[subCategory] = []

                if image_title not in ALL_IMAGES[subCategory]:
                    while True:
                        try:
                            urllib.request.urlretrieve(image_url, os.path.join(image_dir, image_title))
                        except Exception as ex:
                            print("Error when downloading %s. %s\nRetry..." % (image_url, ex))
                            time.sleep(PAGE_LOAD_TIME_MAX)
                        else:
                            ALL_IMAGES[subCategory].append(image_title)
                            break

                break

    return image_list


def buttonClickHandling(driver, index):
    variants = driver.find_element(by=By.CSS_SELECTOR, value="ul").find_elements(by=By.CSS_SELECTOR, value="li")
    variants[index].click()
    while True:
        try:
            driver.find_element(by=By.CSS_SELECTOR, value="ul").find_element(by=By.CSS_SELECTOR, value="li[class*='st-input-clicked']")
        except Exception:
            return
        else:
            time.sleep(PAGE_LOAD_TIME_MIN)


def singleVariation(driver, url, image_dir, category, subCategory):
    dataList = []
    randNo = random.randint(100000, 999999)
    variant_group = driver.find_element(by=By.CSS_SELECTOR, value="div[class='product-variants']").find_element(by=By.CSS_SELECTOR, value="div[class='clearfix product-variants-item']")
    variant_title = variant_group.find_element(by=By.CSS_SELECTOR, value="span[class='control-label']").text
    variant_title = variant_title.split("-")[0].strip()

    try:
        variants = variant_group.find_element(by=By.CSS_SELECTOR, value="ul").find_elements(by=By.CSS_SELECTOR, value="li")
    except Exception:
        return False

    for i in range(0, len(variants)):
        variant_value = variants[i].get_attribute("title")
        buttonClickHandling(driver=variant_group, index=i)
        dataList.append(collectInfo(driver=driver, url=url, image_dir=image_dir, category=category, subCategory=subCategory, attribute_list=[[variant_title, variant_value]], data_type="variation", randNo=randNo))

        variant_group = driver.find_element(by=By.CSS_SELECTOR, value="div[class='product-variants']").find_element(by=By.CSS_SELECTOR, value="div[class='clearfix product-variants-item']")
        variants = variant_group.find_element(by=By.CSS_SELECTOR, value="ul").find_elements(by=By.CSS_SELECTOR, value="li")

    # Insert the main "variable" product
    input_image_list = []
    input_attribute_dict = {"Attribute 1 name": [], "Attribute 1 value(s)": [], "Attribute 2 name": [], "Attribute 2 value(s)": []}
    for data_dict in dataList:
        input_image_list += data_dict["Images_List"]
        for key in input_attribute_dict.keys():
            if data_dict[key] != "" and data_dict[key] not in input_attribute_dict[key]:
                input_attribute_dict[key].append(data_dict[key])

    input_image_list = list(set(input_image_list))  # Using a set to remove duplicates
    dataList.insert(0, collectInfo(driver=driver, url=url, image_dir=image_dir, category=category, subCategory=subCategory, attribute_list=[], data_type="variable", input_image_list=input_image_list, input_attribute_dict=input_attribute_dict, randNo=randNo))

    # Export to CSV
    csvWriter(dataList=dataList)
    return True


def doubleVariations(driver, url, image_dir, category, subCategory):
    dataList = []
    randNo = random.randint(100000, 999999)
    variant_groups = driver.find_element(by=By.CSS_SELECTOR, value="div[class='product-variants']").find_elements(by=By.CSS_SELECTOR, value="div[class='clearfix product-variants-item']")
    variant_1_title = variant_groups[0].find_element(by=By.CSS_SELECTOR, value="span[class='control-label']").text
    variant_1_title = variant_1_title.split("-")[0].strip()

    try:
        variants_1 = variant_groups[0].find_element(by=By.CSS_SELECTOR, value="ul").find_elements(by=By.CSS_SELECTOR, value="li")
    except Exception:
        return False

    for i in range(0, len(variants_1)):
        variant_1_value = variants_1[i].get_attribute("title")
        buttonClickHandling(driver=variant_groups[0], index=i)

        variant_groups = driver.find_element(by=By.CSS_SELECTOR, value="div[class='product-variants']").find_elements(by=By.CSS_SELECTOR, value="div[class='clearfix product-variants-item']")
        if len(variant_groups) > 1:
            variant_2_title = variant_groups[1].find_element(by=By.CSS_SELECTOR, value="span[class='control-label']").text
            variant_2_title = variant_2_title.split("-")[0].strip()

            variants_2 = variant_groups[1].find_element(by=By.CSS_SELECTOR, value="ul").find_elements(by=By.CSS_SELECTOR, value="li")
            for j in range(0, len(variants_2)):
                variant_2_value = variants_2[j].get_attribute("title")
                buttonClickHandling(driver=variant_groups[1], index=j)
                dataList.append(collectInfo(driver=driver, url=url, image_dir=image_dir, category=category, subCategory=subCategory, attribute_list=[[variant_1_title, variant_1_value], [variant_2_title, variant_2_value]], data_type="variation", randNo=randNo))

                variant_groups = driver.find_element(by=By.CSS_SELECTOR, value="div[class='product-variants']").find_elements(by=By.CSS_SELECTOR, value="div[class='clearfix product-variants-item']")
                variants_2 = variant_groups[1].find_element(by=By.CSS_SELECTOR, value="ul").find_elements(by=By.CSS_SELECTOR, value="li")
        else:
            dataList.append(collectInfo(driver=driver, url=url, image_dir=image_dir, category=category, subCategory=subCategory, attribute_list=[[variant_1_title, variant_1_value]], data_type="variation", randNo=randNo))
            variant_groups = driver.find_element(by=By.CSS_SELECTOR, value="div[class='product-variants']").find_elements(by=By.CSS_SELECTOR, value="div[class='clearfix product-variants-item']")

        variants_1 = variant_groups[0].find_element(by=By.CSS_SELECTOR, value="ul").find_elements(by=By.CSS_SELECTOR, value="li")

    # Insert the main "variable" product
    input_image_list = []
    input_attribute_dict = {"Attribute 1 name": [], "Attribute 1 value(s)": [], "Attribute 2 name": [], "Attribute 2 value(s)": []}
    for data_dict in dataList:
        input_image_list += data_dict["Images_List"]
        for key in input_attribute_dict.keys():
            if data_dict[key] != "" and data_dict[key] not in input_attribute_dict[key]:
                input_attribute_dict[key].append(data_dict[key])

    input_image_list = list(set(input_image_list))  # Using a set to remove duplicates
    dataList.insert(0, collectInfo(driver=driver, url=url, image_dir=image_dir, category=category, subCategory=subCategory, attribute_list=[], data_type="variable", input_image_list=input_image_list, input_attribute_dict=input_attribute_dict, randNo=randNo))

    # Export to CSV
    csvWriter(dataList=dataList)
    return True


def collectInfo(driver, url, image_dir, category, subCategory, attribute_list, data_type, randNo, input_image_list=[], input_attribute_dict={}):
    title = driver.find_element(by=By.CSS_SELECTOR, value="h1[class='product_name']").text
    if data_type != "variable":
        price = driver.find_element(by=By.CSS_SELECTOR, value="div[class='current-price']").text
    else:
        price = ""

    try:
        description = driver.find_element(by=By.CSS_SELECTOR, value="div[class='product-description']").text
    except Exception:
        description = ""

    # Get dimension
    short_desc = driver.find_element(by=By.CSS_SELECTOR, value="div[itemprop='description']").text
    # width, height, depth = getDimension(short_desc=short_desc)

    # Get brand
    brand = getBrand(url=url)

    # Download Images
    if data_type != "variable":
        image_list = downloadImages(driver=driver, image_dir=image_dir, subCategory=subCategory)
    else:
        image_list = input_image_list

    # Construct SKU, Name, and Parent
    if data_type == "simple":
        sku = "-".join(url.split("-")[-2:]).strip() + "-" + str(randNo)
        name = title
        parent = ""

    elif data_type == "variable":
        sku = "-".join(url.split("-")[-2:]).strip() + "-" + str(randNo)
        name = title
        parent = ""

    elif data_type == "variation":
        sku = ""
        name = title + " - " + ", ".join([k[1] for k in attribute_list])
        parent = "-".join(url.split("-")[-2:]).strip() + "-" + str(randNo)

    data_dict = {
        "ID": "",
        "Type": data_type,
        "SKU": sku,
        "Name": name,
        "Published": "1",
        "Is featured?": "0",
        "Visibility in catalog": "visible",
        "Short description": short_desc,
        "Description": description,
        "Date sale price starts": "",
        "Date sale price ends": "",
        "Tax status": "taxable",
        "Tax class": "",
        "In stock?": "1",
        "Stock": "",
        "Backorders allowed?": "0",
        "Sold individually?": "0",
        "Weight (lbs)": "",
        "Length (in)": "",
        "Width (in)": "",
        "Height (in)": "",
        "Allow customer reviews?": "1",
        "Purchase note": "",
        "Sale price": "",
        "Regular price": price.replace("$", ""),
        "Categories": "%s, %s > %s" % (category, category, brand) if brand != "" else category,
        "Tags": "%s, %s, %s, %s" % (category, subCategory, brand, title.split(" ")[-1]) if brand != "" else "%s, %s, %s" % (category, subCategory, title.split(" ")[-1]),
        "Shipping class": "",
        "Images": ", ".join(image_list) if data_type == "simple" else image_list[0],
        "Images_List": image_list,
        "Download limit": "",
        "Download expiry days": "",
        "Parent": parent,
        "Grouped products": "",
        "Upsells": "",
        "Cross-sells": "",
        "External URL": "",
        "Button text": "",
        "Position": "0",
        "Woo Variation Gallery Images": "" if data_type == "simple" else ", ".join(image_list[1:]),
        "Attribute 1 name": ", ".join(input_attribute_dict["Attribute 1 name"]) if data_type == "variable" else (attribute_list[0][0] if len(attribute_list) > 0 else ""),
        "Attribute 1 value(s)": ", ".join(input_attribute_dict["Attribute 1 value(s)"]) if data_type == "variable" else (attribute_list[0][1] if len(attribute_list) > 0 else ""),
        "Attribute 1 visible": "1" if data_type == "variable" else "",
        "Attribute 1 global": "1" if data_type == "variable" or len(attribute_list) > 0 else "",
        "Attribute 2 name": ", ".join(input_attribute_dict["Attribute 2 name"]) if data_type == "variable" else (attribute_list[1][0] if len(attribute_list) > 1 else ""),
        "Attribute 2 value(s)": ", ".join(input_attribute_dict["Attribute 2 value(s)"]) if data_type == "variable" else (attribute_list[1][1] if len(attribute_list) > 1 else ""),
        "Attribute 2 visible": "1" if data_type == "variable" else "",
        "Attribute 2 global": "1" if data_type == "variable" or len(attribute_list) > 1 else "",
        "Meta: _wpcom_is_markdown": "",
        "Download 1 name": "",
        "Download 1 URL": "",
        "Download 2 name": "",
        "Download 2 URL": "",
    }
    return data_dict


def main():
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
    else:
        getExistingImages()

    if os.path.exists(ALL_PRODUCT_TXT):
        getExistingProducts()

    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)

    # Using Chrome driver
    option = webdriver.ChromeOptions()
    option.add_argument("--disable-infobars")
    # option.add_argument("start-maximized")
    option.add_argument("--headless")
    option.add_argument("--disable-extensions")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)

    for category, webpage in WEB_PAGE_DICT.items():
        page = START_PAGE
        while True:
            weblink = webpage + "?page=%d" % page
            print("Getting products at %s" % weblink)
            driver.get(weblink)
            time.sleep(PAGE_LOAD_TIME_MAX)

            try:
                driver.find_element(by=By.CSS_SELECTOR, value="article[class='alert alert-warning']")
            except Exception:
                pass
            else:
                break

            body = driver.find_element(by=By.CSS_SELECTOR, value="body")
            products_area = driver.find_element(by=By.CSS_SELECTOR, value="div[id='js-product-list']")
            products = products_area.find_elements(by=By.CSS_SELECTOR, value="div[class*='product_list_item ']")
            product_link = []
            for i in range(0, len(products)):
                while True:
                    try:
                        link = products[i].find_element(by=By.CSS_SELECTOR, value="a[class='product_img_link']")
                    except Exception:
                        body.send_keys(Keys.PAGE_DOWN)
                        time.sleep(PAGE_LOAD_TIME_MAX)
                    else:
                        product_link.append(link.get_attribute("href"))
                        break

            for url in product_link:
                if url in ALL_PRODUCT_LINK:
                    continue

                print("Accessing %s..." % url)
                driver.get(url)
                time.sleep(PAGE_LOAD_TIME_MAX)

                # Get Image directory
                subCategory = url.split("/")[-2]
                image_dir = os.path.join(IMAGE_DIR, subCategory)
                if not os.path.exists(image_dir):
                    os.makedirs(image_dir)

                # Get information for all variations
                try:
                    variant_groups = driver.find_element(by=By.CSS_SELECTOR, value="div[class='product-variants']").find_elements(by=By.CSS_SELECTOR, value="div[class='clearfix product-variants-item']")
                except Exception:
                    print("Warning! Unable to find this product - %s" % url)
                else:
                    if len(variant_groups) == 0:
                        randNo = random.randint(100000, 999999)
                        data_dict = collectInfo(driver=driver, url=url, image_dir=image_dir, category=category, subCategory=subCategory, attribute_list=[], data_type="simple", randNo=randNo)

                        # Export to CSV
                        csvWriter(dataList=[data_dict])
                        success = True

                    elif len(variant_groups) == 1:
                        success = singleVariation(driver=driver, url=url, image_dir=image_dir, category=category, subCategory=subCategory)
                    elif len(variant_groups) == 2:
                        success = doubleVariations(driver=driver, url=url, image_dir=image_dir, category=category, subCategory=subCategory)
                    else:
                        print("Warning! More than 2 variation groups found! %d" % len(variant_groups))
                        success = False

                    if success:
                        ALL_PRODUCT_LINK.append(url)
                        updateProducts(url=url)
                    else:
                        print("Error found at %s!" % url)
            page += 1

    driver.close()


if __name__ == "__main__":
    main()
