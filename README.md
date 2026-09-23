# 这里是Kihana的个人博客  (拼好blog)

#### 用于撰写个人学习日志、学习问题解决方案、兴趣爱好等内容

## 本地预览

```powershell
python -m pip install -r requirements.txt
python -m mkdocs serve
```

部署前可运行 `python -m mkdocs build --strict`。博客页和标签页按文章的 `date.created` 倒序排列；未填写日期的旧文章回退到 Git 创建时间。新文章建议在 front matter 中写明：

```yaml
date:
  created: 2026-09-23
tags:
  - Linux
```

## 恢复备份

本机修改前的源码快照保存在 `backups/`，该目录不会推送到远端。如需恢复，先保存当前改动，再将对应压缩包解压到仓库根目录并覆盖同名文件；构建产物可重新生成。
---

