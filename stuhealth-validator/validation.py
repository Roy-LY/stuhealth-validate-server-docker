import io
import os
import random
import requests
import struct
import sys

from PIL import Image
from PIL import ImageChops
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# 获取图片的dhash


def getImageHash(img: Image) -> bytes:
    img = img.convert('L').resize((17, 16), Image.LANCZOS)
    imgBytes = img.tobytes()
    imgHash = [0 for _ in range(16)]
    for i in range(16):
        for j in range(16):
            if imgBytes[(i << 4) + j] < imgBytes[(i << 4) + j + 1]:
                imgHash[i] |= 1 << j
    return struct.pack('<HHHHHHHHHHHHHHHH', *imgHash)

# 计算两个dhash之间的汉明距离，范围是0-256，越低则图片越相似
# 使用了查表法


def getImageHashDiff(hashA: bytes, hashB: bytes) -> int:
    diff = 0
    for a, b in zip(hashA, hashB):
        diff += (
            0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4,
            1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
            1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
            2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
            1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
            2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
            2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
            3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
            1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
            2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
            2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
            3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
            2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
            3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
            3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
            4, 5, 5, 6, 5, 6, 6, 7, 5, 6, 6, 7, 6, 7, 7, 8,
        )[a ^ b]
        # xored = a ^ b
        # while xored:
        #     diff += 1
        #     xored &= xored - 1
    return diff


def untilFindElement(by: By, value: str):
    def func(d) -> bool:
        try:
            d.find_element(by, value)
            return True
        except NoSuchElementException:
            return False
    return func


def getValidation():
    remoteWebdriver = os.environ.get("STUHEALTH_VALIDATOR_WEBDRIVER_URL")
    if remoteWebdriver == None:
        remoteWebdriver = "http://127.0.0.1:4444"
    # 打开页面
    browser = webdriver.Remote(command_executor=remoteWebdriver)
    browser.get('https://stuhealth.jnu.edu.cn/')
    WebDriverWait(browser, 3).until(untilFindElement(
        By.CSS_SELECTOR, '#captcha .yidun .yidun_bg-img[src^="https://"]'))
    domYidunImg = browser.find_element(
        By.CSS_SELECTOR, '#captcha .yidun .yidun_bg-img')
    domYidunSlider = browser.find_element(
        By.CSS_SELECTOR, '#captcha .yidun .yidun_slider')
    domValidate = browser.find_element(
        By.CSS_SELECTOR, '#captcha input.yidun_input[name="NECaptchaValidate"]')

    # 获取滑动验证码图片
    img = Image.open(io.BytesIO(requests.get(
        domYidunImg.get_attribute('src')).content))
    # print(domYidunImg.get_attribute('src'))
    imgHash = getImageHash(img)
    imgBackground = None
    imgBackgrounds = os.listdir('bgimg')
    random.shuffle(imgBackgrounds)
    for i in imgBackgrounds:
        j = Image.open(f'bgimg/{i}')
        if getImageHashDiff(imgHash, getImageHash(j)) < 32:
            imgBackground = j
            # print(i)
            break
    if imgBackground is None:
        print('Cannot find background.')
        browser.quit()
        sys.exit(-1)

    # 获取滑动位置
    imgDiff = ImageChops.difference(img, imgBackground).convert('L')
    imgDiffBytes = imgDiff.tobytes()
    targetPosX = 0
    targetPixelCount = 0
    for x in range(imgDiff.width):
        for y in range(imgDiff.height):
            if imgDiffBytes[y * imgDiff.width + x] >= 16:
                targetPosX += x
                targetPixelCount += 1
    targetPosX = round(targetPosX / targetPixelCount) - 22
    # print(targetPosX)
    # for y in range(imgDiff.height):
    #     imgDiff.putpixel((targetPosX, y), 0xFFFFFF)
    # imgDiff.save('diff.png')
    targetPosX = targetPosX / 260 * 280

    # 模拟拖拽，时间单位为1/20s，一共150-300+-20ms
    # 只使用匀速就可以了吗？
    actionTime = round((150 + targetPosX / 280 * 150 +
                       random.randint(-20, 20)) / (1000 / 20))
    ac: ActionChains = ActionChains(browser).click_and_hold(domYidunSlider)
    for i in range(actionTime):
        ac = ac.move_by_offset(targetPosX / actionTime, 0).pause(1 / 20)
    ac.release().perform()

    # 成功了吗？
    try:
        WebDriverWait(browser, 2).until(
            lambda d: domValidate.get_attribute('value'))
        print(domValidate.get_attribute('value'))
        return domValidate.get_attribute('value')
    except TimeoutException:
        print("Timeout!")

    browser.quit()
