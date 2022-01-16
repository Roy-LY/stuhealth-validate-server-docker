# stuhealth-validator

用于每日健康打卡验证码的解析API

## 快速上手

```
# 进入目录
$ cd ./stuhealh-validator
# 首次使用安装依赖
$ pip install -r requirements.txt
# 启动API
$ python main.py
```
> **注意**：若不使用兼容Selenium远程Webdriver，需要设置环境变量```STUHEALTH_VALIDATOR_WEBDRIVER_PATH```指向本机FireFox的Webdriver，且需要本机安装有FireFox方可使用。

### Docker
```
# 安装好Docker及Docker Compose环境后直接运行即可
$ docker-compose up -d

# 运行API后即可使用
$ curl -H "Authorization: Bearer mMRZyQJYgwa" -X POST http://127.0.0.1:5555/refreshToken
```

## 注意事项

1. API默认监听 ```127.0.0.1:5555``` 地址，可通过修改环境变量 ```STUHEALTH_VALIDATOR_LISTEN_HOST``` 及 ```STUHEALTH_VALIDATOR_LISTEN_PORT``` 更换容器内的监听地址，并修改 ```docker-compose.yaml``` 的端口映射来更改对宿主机的监听地址。
    * 若使用 ```Docker``` 运行，只需要修改容器对外的端口映射，无需修改环境变量。
    * 若在本机直接运行```main.py```，需要修改环境变量以更改监听地址。

2. API所使用的远程Webdriver通过```STUHEALTH_VALIDATOR_WEBDRIVER_URL```环境变量指定。
    * 若使用 ```Docker Compose``` 运行，无需修改该变量，Compose会自动启动相应的Webdriver容器供API使用。
    * 若使用 ```Docker``` 或直接运行，需要有能够访问的远程Webdriver服务。
    
3. 若不想使用兼容Selenium的远程Webdriver，保持上述环境变量为空并设置```STUHEALTH_VALIDATOR_WEBDRIVER_PATH```环境变量指向本机FireFox的Webdriver。

4. API所使用的验证Token通过```STUHEALTH_VALIDATOR_AUTHORIZATION_TOKEN```环境变量指定。

5. 使用 ```Docker Compose``` 自动运行的Webdriver服务，其并发度通过```SE_NODE_MAX_SESSIONS```环境变量指定。
