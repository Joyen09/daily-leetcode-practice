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
import re

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
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"無法載入配置文件: {e}")
            return {
                'leetcode_api': "https://leetcode.com/api",
                'api_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                'notes_dir': "learning_notes",
                'progress_file': "progress.json"
            }

    def analyze_solution(self, problem_title: str, code: str, tags: List[str]) -> dict:
        """分析解題方案"""
        
        # 分析使用的資料結構
        data_structures = {
            'Array/List': ['List', 'list', '[]', 'array'],
            'Dictionary/Hash Table': ['dict', '{}', 'hashmap', 'hash table'],
            'Set': ['set', 'hashset'],
            'Queue/Deque': ['queue', 'deque', 'collections.deque'],
            'Stack': ['stack', '[]'],
            'Tree': ['TreeNode', 'tree', 'binary tree'],
            'Heap': ['heapq', 'heap', 'priority queue'],
            'Graph': ['graph', 'adjacency', 'vertex', 'edge']
        }
        
        used_structures = []
        for structure, keywords in data_structures.items():
            if any(keyword in code for keyword in keywords):
                used_structures.append(structure)
        
        # 分析時間複雜度
        def analyze_time_complexity(code: str, tags: List[str]) -> str:
            if any('dp' in tag.lower() for tag in tags):
                return "O(n²) - 動態規劃通常需要二維狀態轉移"
            if 'binary search' in ' '.join(tags).lower():
                return "O(log n) - 二分搜尋的標準時間複雜度"
            if re.search(r'for.*for', code):
                return "O(n²) - 包含巢狀迴圈"
            if 'sort' in code or 'sorted' in code:
                return "O(n log n) - 包含排序操作"
            if re.search(r'for|while', code):
                return "O(n) - 包含單層迴圈"
            return "O(1) - 常數時間操作"

        # 分析空間複雜度
        def analyze_space_complexity(code: str, tags: List[str]) -> str:
            if any('dp' in tag.lower() for tag in tags):
                return "O(n²) - 動態規劃通常需要二維陣列儲存狀態"
            if re.search(r'new_array|list\(|dict\(|set\(', code):
                return "O(n) - 需要額外的資料結構儲存資料"
            return "O(1) - 只使用常數額外空間"
        
        # 根據標籤和代碼特徵推斷演算法類型
        algorithm_patterns = {
            'Dynamic Programming': ['dp', 'dynamic', 'memo', 'tabulation'],
            'Greedy': ['greedy', 'maximum', 'minimum'],
            'Divide and Conquer': ['divide', 'merge', 'recursive'],
            'DFS/BFS': ['dfs', 'bfs', 'depth', 'breadth', 'traverse'],
            'Binary Search': ['binary search', 'left, right'],
            'Two Pointers': ['two pointer', 'left, right', 'start, end'],
            'Sliding Window': ['window', 'substring', 'subarray']
        }
        
        algorithms = set(tags)  # 從題目標籤開始
        for algo, keywords in algorithm_patterns.items():
            if any(keyword in code.lower() for keyword in keywords):
                algorithms.add(algo)
        
        # 分析應用場景
        applications = {
            'Dynamic Programming': [
                '背包問題最佳化',
                '資源分配規劃',
                '路徑規劃最佳化'
            ],
            'Graph': [
                '社交網絡分析',
                '網路路由規劃',
                '地圖導航系統'
            ],
            'Tree': [
                '檔案系統結構',
                '組織架構管理',
                '決策樹分析'
            ],
            'Binary Search': [
                '數據庫查詢優化',
                '搜尋引擎實作',
                '機器學習模型調參'
            ],
            'Two Pointers': [
                '資料流處理',
                '序列比對',
                '字串處理優化'
            ],
            'Stack': [
                '編譯器語法分析',
                '瀏覽器歷史記錄',
                '函數調用追蹤'
            ],
            'Queue': [
                '任務排程系統',
                '消息佇列處理',
                '列印工作管理'
            ],
            'Hash Table': [
                '快取系統實作',
                '資料去重處理',
                '資料庫索引優化'
            ]
        }

        # 根據標籤選擇應用場景
        relevant_applications = []
        for tag in algorithms:
            if tag in applications:
                relevant_applications.extend(applications[tag])
        
        return {
            'data_structures': used_structures if used_structures else ['需要根據具體實現確定'],
            'time_complexity': analyze_time_complexity(code, tags),
            'space_complexity': analyze_space_complexity(code, tags),
            'algorithms': list(algorithms) if algorithms else ['需要根據具體實現確定'],
            'applications': relevant_applications[:3] if relevant_applications else ['需要根據具體實現確定']
        }

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
                        topicTags {
                            name
                            slug
                        }
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
            
            if response.status_code != 200:
                self.logger.error(f"API 請求失敗，狀態碼: {response.status_code}")
                return None

            data = response.json()
            if 'data' not in data or 'question' not in data['data']:
                self.logger.error("API 回應格式不正確")
                return None

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
            try:
                if details and details.get('codeSnippets'):
                    for snippet in details['codeSnippets']:
                        if snippet['lang'] == 'Python3':
                            python_code = snippet['code']
                            break
            except Exception as e:
                self.logger.warning(f"無法獲取程式碼模板: {e}")
                # 使用預設模板
            
            # 獲取題目標籤
            tags = []
            try:
                if details and details.get('topicTags'):
                    tags = [tag.get('name', 'Algorithm') for tag in details['topicTags']]
            except Exception as e:
                self.logger.warning(f"無法獲取題目標籤: {e}")
                tags = ['Algorithm']  # 使用預設標籤

        # 題目描述和示例
            content = "無法獲取題目描述"
            sample_test_case = "無示例測試案例"
            try:
                if details:
                    content = details.get('content', content)
                    sample_test_case = details.get('sampleTestCase', sample_test_case)
            except Exception as e:
                self.logger.warning(f"無法獲取題目詳情: {e}")
                # 使用預設值
            
            return Problem(
                id=question_id,
                title=title,
                difficulty=difficulty,
                tags=tags if tags else ['algorithm'],
                solution=python_code,
                explanation=f"""## 題目描述
{content}

## 測試案例
```
{sample_test_case}
```

## 建議解題思路
1. 理解問題需求：
   - 仔細閱讀題目要求
   - 分析輸入輸出格式
   - 注意邊界條件

2. 思考解決方案：
   - 考慮可能的演算法策略
   - 評估時間和空間複雜度
   - 選擇最佳解決方案

3. 實現步驟：
   - 先實現基本功能
   - 處理特殊情況
   - 優化程式碼

4. 測試驗證：
   - 使用題目提供的測試案例
   - 考慮極端情況
   - 驗證解決方案的正確性
""",
                url=problem_url
            )
        except Exception as e:
            self.logger.error(f"獲取題目失敗: {e}")
            raise

    def create_learning_note(self, problem: Problem) -> str:
        """生成學習筆記"""
        # 分析解決方案
        analysis = self.analyze_solution(problem.title, problem.solution, problem.tags)
        
        template = f"""# 每日技術學習筆記 - {datetime.now().strftime('%Y-%m-%d')}

## LeetCode 題目練習
- 題目編號: {problem.id}
- 題目：[{problem.title}]({problem.url})
- 難度：{problem.difficulty}
- 相關標籤：{', '.join(problem.tags)}

{problem.explanation}

### 解題程式碼
```python
{problem.solution}
```

### 學習重點
1. 使用的資料結構：
   - {chr(10) + '   - '.join(analysis['data_structures'])}

2. 時間複雜度分析：
   - {analysis['time_complexity']}

3. 空間複雜度分析：
   - {analysis['space_complexity']}

### 相關延伸學習
1. 相關演算法：
   - {chr(10) + '   - '.join(analysis['algorithms'])}

2. 實際應用場景：
   - {chr(10) + '   - '.join(analysis['applications'])}
"""
        return template
def save_learning_note(self, problem: Problem) -> str:
    """
    保存學習筆記到文件系統
    
    Args:
        problem (Problem): 要保存筆記的題目對象
    
    Returns:
        str: 保存的文件路徑
    """
    # 確保筆記目錄存在
    notes_dir = Path(self.config.get('notes_dir', 'learning_notes'))
    notes_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名：日期_題目ID_題目標題.md
    filename = f"{datetime.now().strftime('%Y%m%d')}_{problem.id}_{problem.title.replace(' ', '_')}.md"
    file_path = notes_dir / filename
    
    try:
        # 生成學習筆記內容
        learning_note = self.create_learning_note(problem)
        
        # 寫入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(learning_note)
        
        # 記錄日誌
        self.logger.info(f"學習筆記已保存：{file_path}")
        
        # 嘗試將筆記加入 Git 版本控制
        try:
            self.repo.index.add(str(file_path))
            self.repo.index.commit(f"Add learning note for {problem.title}")
            self.logger.info(f"筆記已提交到 Git 倉庫")
        except Exception as git_error:
            self.logger.warning(f"無法提交到 Git 倉庫：{git_error}")
        
        return str(file_path)
    
    except Exception as e:
        self.logger.error(f"保存學習筆記時出錯：{e}")
        raise
