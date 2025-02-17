import requests
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import git
import markdown
from bs4 import BeautifulSoup
import yaml
import random

@dataclass
class Problem:
    id: str
    title: str
    difficulty: str
    tags: List[str]
    solution: str
    explanation: str
    url: str

class TechLearningTracker:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.repo = git.Repo(Path.cwd())
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('learning_tracker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_problem_details(self, title_slug: str) -> dict:
    """獲取題目詳細信息，包括描述和示例"""
    try:
        query = """
            query questionData($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    content
                    codeSnippets {
                        lang
                        code
                    }
                    sampleTestCase
                }
            }
        """
        
        url = "https://leetcode.com/graphql"
        response = requests.post(url,
            json={
                'query': query,
                'variables': {'titleSlug': title_slug}
            },
            headers=self.config['api_headers']
        )
        
        data = response.json()
        return data['data']['question']
    except Exception as e:
        self.logger.error(f"獲取題目詳情失敗: {e}")
        return None

    def get_daily_problem(self) -> Problem:
        """獲取每日演算法題目"""
        try:
            response = requests.get(
                "https://leetcode.com/api/problems/all/",
                headers=self.config['api_headers']
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}")
                
            data = response.json()
            if 'stat_status_pairs' not in data:
                raise Exception("Unexpected API response format")
                
            # 隨機選擇一個題目
            problem_data = random.choice(data['stat_status_pairs'])
            
            # 獲取題目詳細信息
            title = problem_data['stat']['question__title']
            title_slug = problem_data['stat']['question__title_slug']
            question_id = str(problem_data['stat']['question_id'])
            difficulty = ['Easy', 'Medium', 'Hard'][problem_data['difficulty']['level']-1]
            problem_url = f"https://leetcode.com/problems/{title_slug}"
            
            # 獲取題目描述和示例代碼
            details = self.get_problem_details(title_slug)
            
            # 獲取 Python 代碼模板
            python_code = "# 請在此實現您的解答\ndef solution():\n    pass"
            if details and 'codeSnippets' in details:
                for snippet in details['codeSnippets']:
                    if snippet['lang'] == 'Python3':
                        python_code = snippet['code']
                        break
            
            # 題目描述和示例
            content = "無法獲取題目描述"
            if details and 'content' in details:
                content = details['content']
                
            sample_test_case = "無示例測試案例"
            if details and 'sampleTestCase' in details:
                sample_test_case = details['sampleTestCase']
            
            return Problem(
                id=question_id,
                title=title,
                difficulty=difficulty,
                tags=['algorithm'],
                solution=python_code,
                explanation=f"""## 題目描述
{content}

## 測試案例
```
{sample_test_case}
```

## 解題思路
[在此記錄您的解題思路]
""",
                url=problem_url
            )
        except Exception as e:
            self.logger.error(f"獲取題目失敗: {e}")
            raise

    def create_learning_note(self, problem: Problem) -> str:
        """生成學習筆記"""
        template = f"""# 每日技術學習筆記 - {datetime.now().strftime('%Y-%m-%d')}

## LeetCode 題目練習
- 題目編號: {problem.id}
- 題目：[{problem.title}]({problem.url})
- 難度：{problem.difficulty}

{problem.explanation}

### 解題程式碼
```python
{problem.solution}
```

### 學習重點
1. 使用的資料結構：
   - [列出使用的主要資料結構]
2. 時間複雜度分析：
   - [分析解法的時間複雜度]
3. 空間複雜度分析：
   - [分析解法的空間複雜度]

### 相關延伸學習
1. 相關演算法：
   - [列出相關的演算法]
2. 實際應用場景：
   - [描述此演算法的實際應用場景]

## 今日技術學習
- 閱讀的技術文章：
- 學習的新技術：
- 遇到的問題和解決方案：

## 明日計劃
- [ ] 準備學習的主題
- [ ] 需要深入研究的問題
- [ ] 技術難點突破計劃
"""
        return template

    def update_learning_progress(self) -> None:
        """更新學習進度"""
        try:
            # 獲取每日題目
            problem = self.get_daily_problem()
            
            # 生成學習筆記
            note_content = self.create_learning_note(problem)
            
            # 保存筆記
            date_str = datetime.now().strftime('%Y-%m-%d')
            notes_dir = Path(self.config['notes_dir'])
            
            # 強制重新創建目錄
            if notes_dir.exists():
                if notes_dir.is_file():
                    notes_dir.unlink()  # 如果是文件則刪除
            
            # 創建目錄
            notes_dir.mkdir(parents=True, exist_ok=True)
                
            note_path = notes_dir / f"note_{date_str}.md"
            
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(note_content)
            
            # 更新進度追蹤
            self.update_progress_tracking(problem)
            
            # 提交到 GitHub
            self.commit_changes(date_str)
            
            self.logger.info(f"成功更新學習進度: {date_str}")
            
        except Exception as e:
            self.logger.error(f"更新學習進度失敗: {e}")
            raise

    def update_progress_tracking(self, problem: Problem) -> None:
        """更新進度追蹤檔案"""
        progress_path = Path(self.config['progress_file'])
        
        if progress_path.exists():
            with open(progress_path, 'r', encoding='utf-8') as f:
                progress = json.load(f)
        else:
            progress = {
                'total_problems': 0,
                'problems_by_difficulty': {'Easy': 0, 'Medium': 0, 'Hard': 0},
                'tags_frequency': {},
                'daily_records': []
            }
        
        # 更新統計
        progress['total_problems'] += 1
        progress['problems_by_difficulty'][problem.difficulty] += 1
        
        for tag in problem.tags:
            progress['tags_frequency'][tag] = progress['tags_frequency'].get(tag, 0) + 1
        
        # 添加每日記錄
        progress['daily_records'].append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'problem_id': problem.id,
            'problem_title': problem.title,
            'difficulty': problem.difficulty,
            'url': problem.url
        })
        
        # 保存更新後的進度
        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

    def commit_changes(self, date_str: str) -> None:
        """提交更改到 GitHub"""
        try:
            self.repo.index.add('*')
            commit_message = f"每日技術學習更新: {date_str}"
            self.repo.index.commit(commit_message)
            origin = self.repo.remote(name='origin')
            origin.push()
            self.logger.info(f"成功提交到 GitHub: {commit_message}")
        except Exception as e:
            self.logger.error(f"GitHub 提交失敗: {e}")
            raise

if __name__ == "__main__":
    config_path = "config.yaml"
    tracker = TechLearningTracker(config_path)
    tracker.update_learning_progress()
