---
hide:
    - navigation
    - footer
nostatistics: True
---


# 留言板
![今日诗词](https://v2.jinrishici.com/one.svg)


<div id="snowflakes-container"></div>
<script>
  // 在LocalStorage中设置不显示雪花效果的标志
  localStorage.setItem('showSnowflakes', 'true');
</script>

<script>
  // 判断LocalStorage中是否设置了显示雪花效果的标志
  if (localStorage.getItem('showSnowflakes') === 'true') {
    var script = document.createElement('script');
    script.src = 'https://www.lanjie100.com/js/snow.user.js';
    document.head.appendChild(script);
  }
</script>
