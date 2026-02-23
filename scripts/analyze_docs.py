#!/usr/bin/env python3
"""
文档分析脚本

功能:
1. 统计文档数量和类型
2. 分析 Sprint 完成率
3. 生成文档覆盖率报告
4. 检测缺失的文档

使用方法:
    python scripts/analyze_docs.py
    python scripts/analyze_docs.py --sprint 1
    python scripts/analyze_docs.py --report
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict


class DocsAnalyzer:
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir)
        self.docs_dir = self.root / "docs"
        self.kanban_file = self.root / "kanban.md"
        
    def analyze_all(self) -> Dict:
        """运行所有分析"""
        return {
            "doc_count": self.count_documents(),
            "sprint_stats": self.analyze_sprints(),
            "coverage": self.calculate_coverage(),
            "missing_docs": self.find_missing_docs(),
            "timestamp": datetime.now().isoformat()
        }
    
    def count_documents(self) -> Dict[str, int]:
        """统计各类文档数量"""
        counts = {
            "prd": 0,
            "tech_design": 0,
            "sprint_summary": 0,
            "research_report": 0,
            "adr": 0,
            "total": 0
        }
        
        if not self.docs_dir.exists():
            return counts
        
        for md_file in self.docs_dir.rglob("*.md"):
            if "templates" in str(md_file):
                continue
            if "INDEX" in md_file.name:
                continue
                
            counts["total"] += 1
            
            if md_file.parent.name == "product":
                counts["prd"] += 1
            elif md_file.parent.name == "tech":
                if "_design" in md_file.name:
                    counts["tech_design"] += 1
            elif md_file.parent.name == "reports":
                if "sprint_" in md_file.name and "_summary" in md_file.name:
                    counts["sprint_summary"] += 1
                elif "_research" in md_file.name or "_report" in md_file.name:
                    counts["research_report"] += 1
            elif md_file.parent.name == "decisions":
                if md_file.name.startswith("adr_"):
                    counts["adr"] += 1
        
        return counts
    
    def analyze_sprints(self) -> List[Dict]:
        """分析 Sprint 数据"""
        sprints = []
        
        if not self.kanban_file.exists():
            return sprints
        
        content = self.kanban_file.read_text(encoding='utf-8')
        
        sprint_pattern = r'## (🏃|✅) Sprint (\d+): (.+?) \((Current|Completed)\)'
        matches = re.finditer(sprint_pattern, content)
        
        for match in matches:
            status_emoji, sprint_num, title, status = match.groups()
            sprint_num = int(sprint_num)
            
            sprint_section = self._extract_sprint_section(content, match.start())
            
            tasks = self._parse_tasks(sprint_section)
            
            sprint_data = {
                "sprint_number": sprint_num,
                "title": title,
                "status": status,
                "tasks": tasks,
                "stats": self._calculate_task_stats(tasks)
            }
            
            sprints.append(sprint_data)
        
        return sorted(sprints, key=lambda x: x["sprint_number"], reverse=True)
    
    def _extract_sprint_section(self, content: str, start_pos: int) -> str:
        """提取 Sprint 章节内容"""
        next_sprint = content.find("## 🏃 Sprint", start_pos + 1)
        next_section = content.find("## 📦", start_pos + 1)
        
        end_pos = len(content)
        if next_sprint != -1:
            end_pos = min(end_pos, next_sprint)
        if next_section != -1:
            end_pos = min(end_pos, next_section)
        
        return content[start_pos:end_pos]
    
    def _parse_tasks(self, sprint_section: str) -> List[Dict]:
        """解析任务列表"""
        tasks = []
        
        task_pattern = r'- \[([ x~])\] \*\*(.+?)\*\*( \(Priority: (P\d+)\))?'
        matches = re.finditer(task_pattern, sprint_section)
        
        for match in matches:
            status_char, title, _, priority = match.groups()
            
            status_map = {
                ' ': 'pending',
                'x': 'done',
                '~': 'in_progress'
            }
            
            tasks.append({
                "title": title,
                "status": status_map.get(status_char, 'unknown'),
                "priority": priority or "P2"
            })
        
        return tasks
    
    def _calculate_task_stats(self, tasks: List[Dict]) -> Dict:
        """计算任务统计数据"""
        total = len(tasks)
        if total == 0:
            return {
                "total": 0,
                "done": 0,
                "in_progress": 0,
                "pending": 0,
                "completion_rate": 0.0
            }
        
        done = sum(1 for t in tasks if t["status"] == "done")
        in_progress = sum(1 for t in tasks if t["status"] == "in_progress")
        pending = sum(1 for t in tasks if t["status"] == "pending")
        
        return {
            "total": total,
            "done": done,
            "in_progress": in_progress,
            "pending": pending,
            "completion_rate": round(done / total * 100, 1)
        }
    
    def calculate_coverage(self) -> Dict[str, float]:
        """计算文档覆盖率"""
        sprints = self.analyze_sprints()
        
        if not sprints:
            return {
                "prd_coverage": 0.0,
                "tech_design_coverage": 0.0,
                "sprint_summary_coverage": 0.0
            }
        
        total_tasks = sum(s["stats"]["total"] for s in sprints)
        
        prd_count = self.count_documents()["prd"]
        tech_design_count = self.count_documents()["tech_design"]
        sprint_summary_count = self.count_documents()["sprint_summary"]
        completed_sprints = sum(1 for s in sprints if s["status"] == "Completed")
        
        return {
            "prd_coverage": round(prd_count / total_tasks * 100, 1) if total_tasks > 0 else 0.0,
            "tech_design_coverage": round(tech_design_count / total_tasks * 100, 1) if total_tasks > 0 else 0.0,
            "sprint_summary_coverage": round(sprint_summary_count / completed_sprints * 100, 1) if completed_sprints > 0 else 0.0
        }
    
    def find_missing_docs(self) -> Dict[str, List[str]]:
        """查找缺失的文档"""
        missing = {
            "prd_without_tech_design": [],
            "tech_design_without_prd": [],
            "completed_sprint_without_summary": []
        }
        
        product_dir = self.docs_dir / "product"
        tech_dir = self.docs_dir / "tech"
        reports_dir = self.docs_dir / "reports"
        
        if product_dir.exists() and tech_dir.exists():
            prd_files = {f.stem for f in product_dir.glob("*.md") if f.name not in ["backlog.md", "milestones.md"]}
            tech_files = {f.stem.replace("_design", "") for f in tech_dir.glob("*_design.md")}
            
            missing["prd_without_tech_design"] = list(prd_files - tech_files)
            missing["tech_design_without_prd"] = list(tech_files - prd_files)
        
        sprints = self.analyze_sprints()
        completed_sprints = [s["sprint_number"] for s in sprints if s["status"] == "Completed"]
        
        if reports_dir.exists():
            summary_files = {int(re.search(r'sprint_(\d+)_summary', f.name).group(1)) 
                           for f in reports_dir.glob("sprint_*_summary.md")}
            missing["completed_sprint_without_summary"] = [
                f"Sprint {n}" for n in completed_sprints if n not in summary_files
            ]
        else:
            missing["completed_sprint_without_summary"] = [f"Sprint {n}" for n in completed_sprints]
        
        return missing
    
    def generate_report(self, output_file: str = None) -> str:
        """生成分析报告"""
        data = self.analyze_all()
        
        report = []
        report.append("# 文档分析报告")
        report.append(f"\n**生成时间**: {data['timestamp']}\n")
        
        report.append("## 📊 文档数量统计\n")
        counts = data["doc_count"]
        report.append(f"- **总文档数**: {counts['total']}")
        report.append(f"- **PRD 文档**: {counts['prd']}")
        report.append(f"- **技术设计文档**: {counts['tech_design']}")
        report.append(f"- **Sprint 总结**: {counts['sprint_summary']}")
        report.append(f"- **调研报告**: {counts['research_report']}")
        report.append(f"- **ADR 文档**: {counts['adr']}\n")
        
        report.append("## 🏃 Sprint 统计\n")
        sprints = data["sprint_stats"]
        if sprints:
            for sprint in sprints[:3]:
                report.append(f"### Sprint {sprint['sprint_number']}: {sprint['title']} ({sprint['status']})\n")
                stats = sprint["stats"]
                report.append(f"- **任务总数**: {stats['total']}")
                report.append(f"- **已完成**: {stats['done']} ({stats['completion_rate']}%)")
                report.append(f"- **进行中**: {stats['in_progress']}")
                report.append(f"- **待开始**: {stats['pending']}\n")
        else:
            report.append("暂无 Sprint 数据\n")
        
        report.append("## 📈 文档覆盖率\n")
        coverage = data["coverage"]
        report.append(f"- **PRD 覆盖率**: {coverage['prd_coverage']}%")
        report.append(f"- **技术设计覆盖率**: {coverage['tech_design_coverage']}%")
        report.append(f"- **Sprint 总结覆盖率**: {coverage['sprint_summary_coverage']}%\n")
        
        report.append("## ⚠️ 缺失文档\n")
        missing = data["missing_docs"]
        
        if missing["prd_without_tech_design"]:
            report.append("### 有 PRD 但缺少技术设计的功能:\n")
            for item in missing["prd_without_tech_design"]:
                report.append(f"- {item}")
            report.append("")
        
        if missing["tech_design_without_prd"]:
            report.append("### 有技术设计但缺少 PRD 的功能:\n")
            for item in missing["tech_design_without_prd"]:
                report.append(f"- {item}")
            report.append("")
        
        if missing["completed_sprint_without_summary"]:
            report.append("### 已完成但缺少总结的 Sprint:\n")
            for item in missing["completed_sprint_without_summary"]:
                report.append(f"- {item}")
            report.append("")
        
        if not any(missing.values()):
            report.append("✅ 所有文档完整!\n")
        
        report_text = "\n".join(report)
        
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_text, encoding='utf-8')
            print(f"报告已保存到: {output_file}")
        
        return report_text


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="分析项目文档")
    parser.add_argument("--sprint", type=int, help="分析特定 Sprint")
    parser.add_argument("--report", action="store_true", help="生成完整报告")
    parser.add_argument("--output", type=str, help="报告输出文件路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    
    args = parser.parse_args()
    
    analyzer = DocsAnalyzer()
    
    if args.json:
        data = analyzer.analyze_all()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.report:
        output = args.output or "docs/reports/doc_analysis.md"
        report = analyzer.generate_report(output)
        print(report)
    elif args.sprint is not None:
        sprints = analyzer.analyze_sprints()
        target_sprint = next((s for s in sprints if s["sprint_number"] == args.sprint), None)
        if target_sprint:
            print(f"\n=== Sprint {target_sprint['sprint_number']}: {target_sprint['title']} ===")
            print(f"状态: {target_sprint['status']}")
            print(f"\n任务统计:")
            stats = target_sprint["stats"]
            print(f"  总数: {stats['total']}")
            print(f"  完成: {stats['done']} ({stats['completion_rate']}%)")
            print(f"  进行中: {stats['in_progress']}")
            print(f"  待开始: {stats['pending']}")
        else:
            print(f"未找到 Sprint {args.sprint}")
    else:
        counts = analyzer.count_documents()
        print("\n=== 文档统计 ===")
        print(f"总文档数: {counts['total']}")
        print(f"PRD: {counts['prd']}")
        print(f"技术设计: {counts['tech_design']}")
        print(f"Sprint 总结: {counts['sprint_summary']}")
        print(f"调研报告: {counts['research_report']}")
        print(f"ADR: {counts['adr']}")
        
        coverage = analyzer.calculate_coverage()
        print("\n=== 文档覆盖率 ===")
        print(f"PRD 覆盖率: {coverage['prd_coverage']}%")
        print(f"技术设计覆盖率: {coverage['tech_design_coverage']}%")
        print(f"Sprint 总结覆盖率: {coverage['sprint_summary_coverage']}%")


if __name__ == "__main__":
    main()
