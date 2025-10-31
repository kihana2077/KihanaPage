# scripts/generate_tag_cloud.py
from wordcloud import WordCloud
import yaml
import glob

# 1. 扫描所有 .md 文件，解析 YAML front matter 中的 tags
tags_list = []
for file_path in glob.glob("docs/**/*.md", recursive=True):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 简单解析 YAML front matter (需要更健壮的解析器，如 frontmatter 库)
        if content.startswith('---'):
            parts = content.split('---')
            if len(parts) >= 2:
                meta = yaml.safe_load(parts[1])
                if meta and 'tags' in meta:
                    tags_list.extend(meta['tags'])

# 2. 统计标签频率
from collections import Counter
tag_counts = Counter(tags_list)

# 3. 生成词云
wc = WordCloud(
    width=800,
    height=400,
    background_color='white',
    font_path='/path/to/chinese-font.ttf' # 重要！指定中文字体路径
).generate_from_frequencies(tag_counts)

# 4. 保存图片
wc.to_file('docs/assets/images/tag-cloud.png')