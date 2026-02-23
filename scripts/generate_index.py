#!/usr/bin/env python3
"""
自动生成文档索引

功能:
1. 扫描 docs/ 目录下的所有文档
2. 按类型分类
3. 生成 docs/INDEX.md

使用方法:
    python scripts/generate_index.py
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class IndexGenerator:
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir)
        self.docs_dir = self.root / "docs"
        
    def scan_documents(self) -> Dict[str, List[Dict]]:
        """扫描所有文档"""
        docs = {
            "product": [],
            "tech": [],
            "reports": [],
            "decisions": [],
            "templates": []
        }
        
        if not self.docs_dir.exists():
            return docs
        
        for md_file in self.docs_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue
            
            rel_path = md_file.relative_to(self.docs_dir)
            category = rel_path.parts[0] if len(rel_path.parts) > 1 else "other"
            
            if category in docs:
                title = self._extract_title(md_file)
                docs[category].append({
                    "path": str(rel_path),
                    "name": md_file.stem,
                    "title": title
                })
        
        for category in docs:
            docs[category].sort(key=lambda x: x["name"])
        
        return docs
    
    def _extract_title(self, file_path: Path) -> str:
        """从文档中提取标题"""
        try:
            content = file_path.read_text(encoding='utf-8')
            match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()
        except Exception:
            pass
        return file_path.stem
    
    def generate_index(self) -> str:
        """生成索引内容"""
        docs = self.scan_documents()
        
        lines = []
        lines.append("# 文档索引")
        lines.append("")
        lines.append("> 本文档提供项目所有文档的快速导航。按文档类型分类,包含文档描述和链接。")
        lines.append("")
        lines.append(f"**最后更新**: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        
        lines.append("## 📚 文档分类")
        lines.append("")
        
        lines.append("### 🎯 产品文档 (Product Documents)")
        lines.append("")
        if docs["product"]:
            for doc in docs["product"]:
                if doc["name"] in ["backlog", "milestones"]:
                    lines.append(f"*   **[{doc['title']}]({doc['path']})**: 核心产品文档")
                else:
                    lines.append(f"*   [{doc['title']}]({doc['path']})")
        else:
            lines.append("*   暂无产品文档")
        lines.append("")
        lines.append("> 💡 **提示**: 使用 [prd_standard.md](templates/prd_standard.md) 或 [prd_lightweight.md](templates/prd_lightweight.md) 模板创建新 PRD")
        lines.append("")
        
        lines.append("### 🏗️ 技术文档 (Technical Documents)")
        lines.append("")
        if docs["tech"]:
            for doc in docs["tech"]:
                lines.append(f"*   [{doc['title']}]({doc['path']})")
        else:
            lines.append("*   暂无技术文档")
        lines.append("")
        lines.append("> 💡 **提示**: 使用 [tech_design.md](templates/tech_design.md) 模板创建新技术设计文档")
        lines.append("")
        
        lines.append("### 📊 Sprint 管理 (Sprint Management)")
        lines.append("")
        lines.append("#### 当前 Sprint")
        lines.append("")
        lines.append("*   **[Kanban](../kanban.md)**: 项目任务看板,SSOT (单一事实来源)")
        lines.append("")
        lines.append("#### Sprint 报告")
        lines.append("")
        if docs["reports"]:
            sprint_reports = [d for d in docs["reports"] if "sprint" in d["name"] and "summary" in d["name"]]
            if sprint_reports:
                for doc in sprint_reports:
                    lines.append(f"*   [{doc['title']}]({doc['path']})")
            else:
                lines.append("*   暂无 Sprint 报告")
        else:
            lines.append("*   暂无 Sprint 报告")
        lines.append("")
        lines.append("> 💡 **提示**: 使用 [sprint_summary.md](templates/sprint_summary.md) 模板创建 Sprint 总结")
        lines.append("")
        
        lines.append("### 🔍 调研报告 (Research Reports)")
        lines.append("")
        if docs["reports"]:
            research_reports = [d for d in docs["reports"] if "research" in d["name"] or "report" in d["name"]]
            if research_reports:
                for doc in research_reports:
                    lines.append(f"*   [{doc['title']}]({doc['path']})")
            else:
                lines.append("*   暂无调研报告")
        else:
            lines.append("*   暂无调研报告")
        lines.append("")
        lines.append("> 💡 **提示**: 使用 [research_report.md](templates/research_report.md) 模板创建调研报告")
        lines.append("")
        
        lines.append("### 📝 模板库 (Templates)")
        lines.append("")
        if docs["templates"]:
            for doc in docs["templates"]:
                lines.append(f"*   **[{doc['title']}]({doc['path']})**")
        lines.append("")
        
        lines.append("## 🔗 文档关系图")
        lines.append("")
        lines.append("```mermaid")
        lines.append("graph TD")
        lines.append("    A[Milestones] --> B[Backlog]")
        lines.append("    B --> C[Sprint Planning]")
        lines.append("    C --> D[Kanban]")
        lines.append("    D --> E[PRD]")
        lines.append("    E --> F[Tech Design]")
        lines.append("    F --> G[Code Implementation]")
        lines.append("    G --> H[Sprint Summary]")
        lines.append("    H --> B")
        lines.append("```")
        lines.append("")
        
        lines.append("## 🔍 快速搜索")
        lines.append("")
        lines.append("### 按关键词搜索")
        lines.append("")
        lines.append("使用以下命令搜索文档内容:")
        lines.append("")
        lines.append("```bash")
        lines.append("# 搜索包含特定关键词的文档")
        lines.append('grep -r "关键词" docs/')
        lines.append("")
        lines.append("# 搜索 PRD 文档")
        lines.append('find docs/product -name "*.md" -type f')
        lines.append("")
        lines.append("# 搜索技术设计文档")
        lines.append('find docs/tech -name "*_design.md" -type f')
        lines.append("```")
        lines.append("")
        
        lines.append("## 📚 相关资源")
        lines.append("")
        lines.append("*   **[文档管理指南](DOCUMENTATION_GUIDE.md)**: 文档撰写和管理的最佳实践")
        lines.append("*   **[项目 README](../README.md)**: 项目整体介绍")
        lines.append("*   **[技能目录](../skills/)**: Agent Skills 技能列表")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("**维护说明**: 本索引通过 `python scripts/generate_index.py` 自动生成。")
        
        return "\n".join(lines)
    
    def save_index(self):
        """保存索引文件"""
        index_content = self.generate_index()
        index_file = self.docs_dir / "INDEX.md"
        index_file.write_text(index_content, encoding='utf-8')
        print(f"索引已生成: {index_file}")


def main():
    generator = IndexGenerator()
    generator.save_index()


if __name__ == "__main__":
    main()
