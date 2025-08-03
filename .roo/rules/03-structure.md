# 代码结构指南

## 1. 引言

欢迎来到 Open WebUI 项目！本文档旨在详细介绍本项目的代码结构，帮助新成员快速熟悉代码库，并为现有成员提供一个统一的参考标准。

本项目采用前后端分离的架构：
*   **后端:** 基于 **Python**（可能使用 FastAPI 或类似框架），负责处理核心业务逻辑、API 服务以及与数据库的交互。
*   **前端:** 基于 **SvelteKit**，构建了一个响应式、交互友好的用户界面。

## 2. 顶层目录结构

项目的根目录包含以下几个核心文件夹：

*   [`backend/`](../backend/): 存放所有后端服务的源代码。
*   [`src/`](../src/): 存放所有 SvelteKit 前端的源代码。
*   [`docs/`](../docs/): 存放项目相关的文档，包括本篇指南。
*   [`cypress/`](../cypress/): 包含所有 Cypress 端到端（E2E）测试用例。
*   [`kubernetes/`](../kubernetes/): 存放用于部署到 Kubernetes 环境的配置文件，例如 Helm Charts。
*   [`scripts/`](../scripts/): 包含一些用于开发和部署的辅助脚本。
*   [`static/`](../static/): 存放全局静态资源，如网站图标（favicon）和图片。

## 3. 后端 (`backend/open_webui`)

后端代码遵循模块化的设计原则，核心功能分布在以下目录中：

*   [`routers/`](../backend/open_webui/routers/): 定义了所有 API 的路由。每个文件对应一个资源或功能模块（例如 `chats.py`, `users.py`），负责处理 HTTP 请求。
*   [`models/`](../backend/open_webui/models/): 包含应用程序的数据模型，通常是与数据库表对应的 ORM 模型。
*   [`retrieval/`](../backend/open_webui/retrieval/): 负责实现检索增强生成（RAG）功能。它包含了从不同数据源（如文档、网页）加载、处理和检索信息的逻辑。
*   [`utils/`](../backend/open_webui/utils/): 存放后端通用的工具函数和辅助类，以供不同模块复用。
*   [`migrations/`](../backend/open_webui/migrations/): 存放数据库迁移脚本，用于管理数据库结构的版本变更。
*   [`static/`](../backend/open_webui/static/): 存放由后端服务直接提供的静态文件，例如 Swagger UI 界面。
*   [`socket/`](../backend/open_webui/socket/): 处理 WebSocket 相关的功能，用于实现实时通信。

## 4. 前端 (`src`)

前端使用 SvelteKit 框架，其目录结构清晰且符合社区最佳实践：

*   [`routes/`](../src/routes/): SvelteKit 的核心，采用基于文件的路由系统。此目录下的文件和文件夹结构直接映射到应用的 URL 路径。
*   [`lib/`](../src/lib/): 前端应用的核心代码库。
    *   [`lib/components/`](../src/lib/components/): 存放可复用的 Svelte 组件。组件按功能域（如 `chat`, `admin`, `common`）进行组织。
    *   [`lib/apis/`](../src/lib/apis/): 封装了与后端 API 的所有交互。每个文件对应一个后端资源，提供了类型安全的请求函数。
    *   [`lib/stores/`](../src/lib/stores/): 定义了用于全局状态管理的 Svelte Stores。
    *   [`lib/utils/`](../src/lib/utils/): 存放前端通用的工具函数和辅助模块。
    *   [`lib/i18n/`](../src/lib/i18n/): 负责国际化（i18n）功能，包含所有语言的翻译文件。
    *   [`lib/types/`](../src/lib/types/): 存放 TypeScript 的类型定义，用于增强代码的健壮性。

## 5. 总结

清晰、一致的代码结构是项目可维护性和可扩展性的基石。希望本指南能帮助团队成员高效地协作。

请在代码结构发生显著变化时，及时更新此文档，以确保其准确性。