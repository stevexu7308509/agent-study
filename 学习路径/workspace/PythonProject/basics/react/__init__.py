"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   react/__init__.py — 包初始化文件                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

=== 作用 ===
这个文件让 Python 把 react/ 目录识别为一个包（package），
从而可以使用 from react import ReActAgent 这样的导入方式。

如果没有 __init__.py，react/ 只是一个普通目录，
Python 不会把它当成包（Python 3.3+ 有隐式命名空间包，但显式的更明确）。

Java 类比:
  这相当于 Java 中的 package com.example.react;
  __init__.py 文件本身 = package-info.java

=== 当前为空 ===
这是最小化的 __init__.py，只做"标记包"的用途。
后续可以在 __init__.py 中:
  - 导出公共 API: from .ReAct import ReActAgent
  - 定义包级变量
  - 执行包初始化代码
"""
