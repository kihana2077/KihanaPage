# Github Pages文档自动化部署
在考虑自动化部署时遇到了十分多的问题  
比如部署失败、部署后CNAME解析失效等，有些问题我参照了[秋叶亚里沙](https://blog.arisa.moe/blog/2022/220407-github-pages/)大佬的解决方法

此外，我使用的自动创建时间日期与作者的插件，还需要在workflow中添加`pip install mkdocs-document-dates`**来确保在构建时能正确引用库**