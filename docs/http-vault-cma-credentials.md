# 从 HTTP 请求理解 Vault 与 CMA Credential Type

理解认证链路时，最容易出现的问题不是某个概念太难，而是把三个不同层次的问题混在了一起：

1. HTTP 请求用哪个字段携带认证信息；
2. 真实凭证如何被安全保存；
3. 平台按什么模式管理和使用凭证。

正确的理解顺序应该是：先看 HTTP 请求的结构，再看 Vault 的职责，最后理解 CMA 的 credential type。

## 1. 地基层：HTTP 请求如何携带认证信息

一个 HTTP 请求通常由 URL、Headers 和 Body 等部分组成：

```text
一个 HTTP 请求
├── URL
├── Headers
│   ├── Authorization: Bearer xxx
│   ├── Cookie: session=xxx
│   └── X-Api-Key: xxx
└── Body
```

`Authorization`、`Cookie` 和 `X-Api-Key` 都是 HTTP Header 字段。它们表示的是：**请求发出时，认证信息最终放在哪个字段中**。

常见形式如下：

```http
Authorization: Bearer <access-token>
```

```http
Cookie: session=<session-id>
```

```http
X-Api-Key: <api-key>
```

需要注意：

- `Authorization` 是标准请求头，Bearer Token 常放在这里；
- `Cookie` 是标准请求头，可以携带会话标识；
- `X-Api-Key` 是常见的自定义请求头名称，实际名称由服务端约定；
- 具体使用哪个字段，由目标服务（例如 Mars）的 API 协议决定，而不是由 Vault 决定。

这一层只回答一个问题：**服务端期望在请求的什么位置收到什么值？**

## 2. 安全存储层：Vault 做什么

Vault 的核心职责是安全保存真实 secret，例如：

- Access Token；
- API Key；
- Session Secret；
- OAuth Client Secret；
- 用户名和密码等敏感信息。

可以把它简化为：

```text
Vault
= 负责保存请求中 xxx 对应的真实秘密
```

Agent 或大模型不需要、也不应该直接看到 secret 的明文。它们可以引用某个凭证，但读取和注入真实值的动作应由受信任的平台组件完成。

Vault 通常不负责定义 HTTP 认证协议。它解决的是：

> secret 存在哪里、谁可以访问、如何避免明文暴露。

因此，Vault 与 `Authorization`、`Cookie`、`X-Api-Key` 不是同一类概念：前者是安全存储机制，后者是 HTTP 请求字段。

## 3. 管理与使用层：CMA Credential Type 是什么

CMA 的 credential type 描述的是：**平台以后按什么模式管理、获取和使用一份凭证**。

它们不是三种 HTTP Header。

### 3.1 `static_bearer`

`static_bearer` 表示平台管理一份相对固定的 Bearer Token。发起请求时，受信任组件通常会把它组装成：

```http
Authorization: Bearer <token-from-vault>
```

因此：

- `static_bearer` 是凭证管理/使用模式；
- `Authorization` 是最终承载该凭证的 HTTP Header；
- Vault 保存的是实际 Token。

### 3.2 `mcp_oauth`

`mcp_oauth` 表示凭证通过 OAuth 流程获得和维护。平台可能需要处理授权、Access Token、刷新以及过期等问题。

OAuth 最终获得的 Access Token 在常见场景中仍会进入 HTTP 请求，例如：

```http
Authorization: Bearer <oauth-access-token>
```

所以，`mcp_oauth` 回答的是“Token 如何获得和维护”，而 `Authorization` 回答的是“Token 发请求时放在哪里”。最终位置仍应以目标服务的协议和平台实现为准。

### 3.3 `environment_variable`

`environment_variable` 表示平台以环境变量的方式向受控运行环境提供某个凭证，例如：

```text
MARS_API_KEY=<secret-from-vault>
```

环境变量只是凭证的交付方式，不等于 HTTP Header，也不等于 Cookie。应用代码拿到环境变量后，仍需根据目标 API 的要求构造请求：

```text
环境变量 MARS_API_KEY
        │
        ▼
应用读取 secret
        │
        ├──► X-Api-Key: <secret>
        ├──► Authorization: Bearer <secret>
        └──► Cookie: session=<secret>
             （具体选择由 API 协议决定）
```

因此，`environment_variable` 和 Cookie 没有固定对应关系。只有当应用代码明确把环境变量中的值写入 `Cookie` Header 时，两者才会在一次具体请求中建立联系。

## 4. 三层概念对照

| 层次 | 关注的问题 | 例子 |
| --- | --- | --- |
| HTTP 协议层 | 凭证在请求中放哪里 | `Authorization`、`Cookie`、`X-Api-Key` |
| 安全存储层 | 真实 secret 存在哪里 | Vault |
| CMA 管理层 | 平台如何获取、维护或交付凭证 | `static_bearer`、`mcp_oauth`、`environment_variable` |

不要把跨层概念直接等同：

```text
static_bearer       ≠ Authorization Header
mcp_oauth           ≠ 某个固定 Header
环境变量             ≠ Cookie
Vault                ≠ HTTP 认证方式
```

但它们可以在一次请求中协作：

```text
CMA 决定凭证使用模式
        │
        ▼
Vault 保存真实 secret
        │
        ▼
受信任组件获取或注入 secret
        │
        ▼
HTTP 客户端按 Mars API 协议构造 Header
```

## 5. 从 Agent 到 Mars：一次请求经历什么

下面用一条通用链路串起三个层次。实际组件边界和注入位置可能因平台实现而不同，但职责划分保持一致。

### 第一步：Agent 表达调用意图

Agent 决定调用 Mars 的某个能力，并产生非敏感的请求信息，例如：

- 调用哪个 endpoint；
- 使用哪种方法（GET、POST 等）；
- 发送什么业务参数；
- 引用哪个已配置的 credential。

Agent 不需要拿到真实 secret。

### 第二步：CMA 解析 credential type

平台读取该 credential 的类型，并决定后续处理方式：

- `static_bearer`：使用已保存的静态 Token；
- `mcp_oauth`：使用 OAuth Access Token，必要时按机制刷新；
- `environment_variable`：把 secret 提供给受控运行环境，由应用读取。

### 第三步：受信任组件访问 Vault

具备权限的平台组件从 Vault 获取所需 secret。这个过程应避免把明文写入：

- 大模型上下文；
- Agent 可见消息；
- 普通应用日志；
- 错误栈和调试输出。

### 第四步：HTTP 客户端构造请求

受信任组件或应用代码按照 Mars API 契约，把凭证放到正确位置。例如：

```http
POST /v1/tasks HTTP/1.1
Host: mars.example.com
Authorization: Bearer <injected-secret>
Content-Type: application/json

{"name":"example"}
```

这里的 `Authorization` 属于 HTTP 协议层；`<injected-secret>` 可能来自 Vault；平台选择并维护它的方式由 CMA credential type 描述。

### 第五步：Mars 验证并响应

Mars 从约定的 Header 中读取凭证，完成签名、Token、Session 或 API Key 校验。通过后处理业务请求，否则返回 `401 Unauthorized` 或 `403 Forbidden` 等响应。

### 第六步：响应返回 Agent

平台把业务响应交给 Agent，同时继续保护凭证，避免在响应处理、观测数据或日志中泄露 secret。

完整链路可以概括为：

```text
Agent
  │  提供调用意图和 credential 引用，不接触明文
  ▼
CMA
  │  决定凭证的管理/使用模式
  ▼
受信任的凭证组件 ─────► Vault
  │                     读取真实 secret
  │  按目标 API 契约注入凭证
  ▼
HTTP 请求（Authorization / Cookie / X-Api-Key ...）
  │
  ▼
Mars
  │  验证凭证并处理请求
  ▼
业务响应
```

## 6. 判断一个认证配置时，依次问三个问题

遇到新场景时，按下面的顺序分析：

1. **Mars 的 API 契约是什么？** 先确认它要求 `Authorization`、`Cookie`、`X-Api-Key`，还是其他位置和格式。
2. **真实 secret 保存在哪里？** 确认由 Vault 等安全设施保存，避免进入模型上下文和日志。
3. **平台如何管理和交付它？** 再选择 `static_bearer`、`mcp_oauth` 或 `environment_variable` 等合适的 credential type。

先分层，再串联，就不会再把“Header 放在哪里”“secret 存在哪里”和“平台如何使用凭证”混为一谈。
