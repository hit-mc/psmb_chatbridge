# PSMB Chatbridge

## 简介


这是一个基于PSMB协议的跨服聊天BOT（MC服务器端，MCDR插件）。

播报多个BC子服之间的聊天内容，以及将聊天内容转发到外置机器人中。这个项目的将进一步增强跨服聊天的功能，实现死亡信息、成就信息等等其他有趣的信息转发服务。


## 使用方法

### 安装MCDR插件

安装这个插件有两种方法，分别是从打包好的文件安装，和直接安装成目录
#### 从打包好的文件安装

我们的仓库集成了MCDR构建功能，你可以在[这里](https://github.com/hit-mc/psmb_chatbridge/actions)找到所有的构建版本。但注意，不是每一个版本都是稳定的。你可能需要选择具有tag的版本或者在Release中的版本。

### 直接安装目录

这个git仓库本身，即可clone成插件。你只需要在mcdr目录下，找到plugins目录。然后clone本仓库，即可完成。

### 书写配置文件

配置文件是json格式的，通常来说是`config/psmb_chatbridge/config.json`。

```json
{
    "psmb_host": "127.0.0.1",
    "psmb_port": 13880,
    "psmb_pub_topic": "gglobal",
    "psmb_sub_id_pattern": "gglobal",
    "psmb_enable_tls": false,
    "client_id": 1,
    "enable_tls": false,
    "client_name": "survival"
}
```

我们将每一个交换信息的主体看做一个**客户端**，客户端间应该有ID和名字。客户端ID不应该重复，命名客户端通常按照如下方法：

|  实际信息主体   | 建议命名  |
|  ----  | ----  |
| 生存服务器  | survival |
| 镜像服务器  | mirror |
| 创造服务器 | creative |
| QQ机器人 | qqbot |


## 对接PSMB服务器

PSMB本身负责在多个客户端间转送数据流。一个比较好的PSMB服务器实现可以参考本组织下的`pypsmb`仓库。其中有相关的协议说明和python实现。


## QQ机器人的使用方法

见[这个仓库](https://github.com/hit-mc/nonebot-crosslink-client)

