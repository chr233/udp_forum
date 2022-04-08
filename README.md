# -

## 指令表

| 指令 | 全名           | 示例                       | 说明         | 回显                            |
| ---- | -------------- | -------------------------- | ------------ | ------------------------------- |
| CRT  | Create Thread  | CRT 帖子标题               | 创建帖子     |                                 |
| LST  | List Threads   | LST                        | 列出所有帖子 |                                 |
| MSG  | Post Message   | MSG 帖子标题 消息          | 发送回复     | messagenumber username: message |
| EDT  | Edit Message   | EDT 帖子标题 回帖序号 消息 | 编辑回复     |                                 |
| DLT  | Delete Message | DLT 帖子标题 回帖序号      | 删除回复     |                                 |
| RDT  | Read Thread    | RDT 帖子标题               | 获取帖子回复 |                                 |
| UPD  | Upload file    | UPD 帖子标题 文件名        | 上传文件     | Username uploaded filename      |
| DWN  | Download file  | DWN 帖子标题 文件名        | 下载文件     |                                 |
| RMV  | Remove Thread  | RMV 帖子标题               | 删除帖子     |                                 |
| XIT  | Exit           | XIT                        | 退出         |                                 |

## 通讯协议

通讯流程:

```txt
客户端发起请求
鉴权获取 token
凭借 token 调用服务端 API,
接收到服务端返回结果后, 需要返回一个 meta 消息, 告知服务端已收到消息
如果服务端未收到 meta 消息将触发超时重传

如果重传失败将会判定为客户端离线, 此时 token 失效需要重新登陆

根据 echo 区分不同的请求
根据 token 区分不同的用户
```

### 元事件

客户端用于测试服务端是否在线, 服务端会返回元事件包
客户端用于告知服务端已收到消息

请求和返回格式相同

```json
{
  "meta": true,
  "echo": "",
  "reply": true
}
```

### 错误处理

- 错误信息

```json
{
  "code": 200,
  "msg": "",
  "error": "",
  "echo": ""
}
```

### 鉴权

#### 登录

- 请求

```json
{
  "cmd": "LOG",
  "user": "",
  "passwd": "",
  "echo": ""
}
```

- 返回

```json
{
  "code": 200,
  "msg": "",
  "token": "",
  "echo": ""
}
```

#### 注册

- 请求

```json
{
  "cmd": "REG",
  "user": "",
  "passwd": "",
  "echo": ""
}
```

- 返回

```json
{
  "code": 200,
  "msg": "",
  "token": "",
  "echo": ""
}
```

### 消息交换

- 请求

```json
{
  "cmd": "LST",
  "args": "",
  "token": "",
  "echo": ""
}
```

- 返回

```json
{
  "code": "200",
  "msg": "",
  "data": "",
  "echo": ""
}
```

### 文件交换

- 请求

```json
{
  "cmd": "UPD",
  "args": "",
  "name":"",
  "body":"",
  "token":"",
  "echo":""
}
```

- 响应

```json
{
  "code": "200",
  "msg": "",
  "name":"",
  "body":"",
  "echo": ""
}
```

## 测试用例

```txt
{"meta":true,"echo":"","reply":true}

{"cmd":"LOG","user":"","passwd":"","echo":""}

{"cmd":"LST","args":[],"token":"","echo":""}
```

输出示例

```txt
user> LST
<wait response ...>
```
