---
tags:
    - Github
    - GithubPages
    - 博客
    - Mkdocs
---
# Github Pages文档自动化部署
在考虑自动化部署时遇到了十分多的问题  
比如部署失败、部署后CNAME解析失效等，有些问题我参照了[秋叶亚里沙](https://blog.arisa.moe/blog/2022/220407-github-pages/)大佬的解决方法

此外，我使用的自动创建时间日期与作者的插件，还需要在workflow中添加`pip install mkdocs-document-dates`**来确保在构建时能正确引用库**

## 更新
在mkdocs创建友链时想要直接引用库里的图片而不直接引用图片库链接，因为在网络环境下经常出现无法加载    
使用的是html引用图片 
在尝试多次绝对路径之后都不行，于是改为相对路径，我的图片直接放在assets文件夹里，则需要改为../assets/picture.png