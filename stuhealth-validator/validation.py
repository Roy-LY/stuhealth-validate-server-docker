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

# 计算多项式，每一项是pn * (x ** n)
def polynomialCalc(x: float, params: tuple[float]) -> float:
    return sum(p * (x ** n) for n, p in enumerate(params))


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
    #browser = webdriver.Chrome("/Users/samersions/Documents/Development/loginSschoolNetwork/driver/chromedriver")
    browser.get('https://stuhealth.jnu.edu.cn/')
    WebDriverWait(browser, 3).until(untilFindElement(By.CSS_SELECTOR, '#captcha .yidun .yidun_bg-img[src^="https://"]'))
    domYidunImg = browser.find_element(By.CSS_SELECTOR, '#captcha .yidun .yidun_bg-img')
    domYidunSlider = browser.find_element(By.CSS_SELECTOR, '#captcha .yidun .yidun_slider')
    domValidate = browser.find_element(By.CSS_SELECTOR, '#captcha input.yidun_input[name="NECaptchaValidate"]')

    # 获取滑动验证码图片
    img = Image.open(io.BytesIO(requests.get(domYidunImg.get_attribute('src').replace('@2x', '').replace('@3x', '')).content))
    # print(domYidunImg.get_attribute('src'))
    imgHash = getImageHash(img)
    imgBackground = min(
        (Image.open(f'bgimg/{i}') for i in os.listdir('bgimg')),
        key=lambda i: getImageHashDiff(imgHash, getImageHash(i)),
    )

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
    #print(targetPosX)
    #for y in range(imgDiff.height):
    #    imgDiff.putpixel((targetPosX, y), 0xFFFFFF)
    #imgDiff.save('tmp/diff.png')
    targetPosX = targetPosX / 260 * 270

    # 模拟拖拽，时间单位为1/50s也就是20ms，一共500-1000+-200ms
    # 另外鼠标放到滑块上等待300-500ms，松开再等待50-100ms
    # 拟合拖拽轨迹的多项式定义域和值域均为[0, 1]，且f(0)=0 f(1)=1
    polynomial = random.choice((
        (0, 7.27419, -23.0881, 40.86, -40.2374, 20.1132, -3.922),
        (0, 11.2642, -54.1671, 135.817, -180.721, 119.879, -31.0721),
        (0, 7.77852, -37.3727, 103.78, -155.152, 115.664, -33.6981),
        (0, 12.603, -61.815, 159.706, -227.619, 166.648, -48.5237),
    ))
    actionTime = round((500 + targetPosX / 270 * 1000 + random.randint(-200, 200)) / 20)
    targetSeq = tuple(round(polynomialCalc(x / (actionTime - 1), polynomial) * targetPosX) for x in range(actionTime))
    ac: ActionChains = ActionChains(browser, 20).click_and_hold(domYidunSlider).pause(random.randint(300, 500) / 1000)
    for i in range(len(targetSeq) - 1):
        ac = ac.move_by_offset(targetSeq[i + 1] - targetSeq[i], 0)
    ac.pause(random.randint(50, 100) / 1000).release().perform()

    # 成功了吗？
    try:
        WebDriverWait(browser, 2).until(lambda d: domValidate.get_attribute('value'))
    except TimeoutException:
        print("Why timeout?")
    validate = domValidate.get_attribute('value')
    browser.quit()
    if validate:
        print("Well done mein freund!")
        return validate
    else:
        print("What's gong on?")
        return None
