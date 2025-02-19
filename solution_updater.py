import os
import re
from pathlib import Path
import logging
from typing import Optional, Dict
from datetime import datetime
import json

class SolutionUpdater:
    def __init__(self):
        """初始化解題更新器"""
        self.setup_logging()
        
    def setup_logging(self):
        """設置日誌"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('solution_updater.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def extract_problem_info(self, content: str) -> Dict:
        """從筆記內容中提取題目信息"""
        info = {}
        
        # 提取題目編號和標題
        title_match = re.search(r'題目編號: (\d+)\n- 題目：\[(.*?)\]', content)
        if title_match:
            info['id'] = title_match.group(1)
            info['title'] = title_match.group(2)
            
        # 提取難度
        difficulty_match = re.search(r'難度：(\w+)', content)
        if difficulty_match:
            info['difficulty'] = difficulty_match.group(1)
        
        # 提取相關標籤
        tags_match = re.search(r'相關標籤：(.*?)\n', content)
        if tags_match:
            info['tags'] = [tag.strip() for tag in tags_match.group(1).split(',')]
            
        return info

    def generate_solution_template(self, problem_info: Dict) -> str:
        """生成解題思路和模板"""
        # 根據題目類型生成對應的解題模板
        solution_templates = {
            'Array': self._generate_array_solution,
            'Dynamic Programming': self._generate_dp_solution,
            'Tree': self._generate_tree_solution,
            'Graph': self._generate_graph_solution
        }
        
        # 根據標籤選擇模板
        for tag in problem_info.get('tags', []):
            if tag in solution_templates:
                return solution_templates[tag](problem_info)
        
        # 默認模板
        return self._generate_default_solution(problem_info)

    def _generate_array_solution(self, info: Dict) -> str:
        return f"""## 解題分析
這是一個數組相關的問題，我們需要重點關注：
1. 數組的遍歷方式
2. 元素的處理順序
3. 邊界條件的處理

## 解題思路
1. 對數組進行預處理：
   - 檢查邊界條件
   - 考慮排序的必要性
   
2. 主要解題步驟：
   - 使用適當的遍歷策略
   - 處理特殊情況
   - 優化性能

## 建議程式碼實現
```python
def solution(self, nums: List[int]) -> int:
    # 邊界檢查
    if not nums:
        return 0
        
    # 主要邏輯
    result = 0
    for num in nums:
        # TODO: 實現具體邏輯
        pass
        
    return result
```

## 複雜度分析
- 時間複雜度：O(n) - 需要遍歷整個數組
- 空間複雜度：O(1) - 只使用常數額外空間

## 優化建議
1. 考慮使用雙指針技巧
2. 可以使用哈希表優化查找
3. 注意特殊情況的處理
"""

    def _generate_dp_solution(self, info: Dict) -> str:
        return f"""## 解題分析
這是一個動態規劃問題，需要考慮：
1. 狀態定義
2. 轉移方程
3. 初始化條件
4. 結果計算

## 解題思路
1. 定義 DP 數組：
   - 確定狀態維度
   - 明確狀態含義
   
2. 實現步驟：
   - 初始化 DP 數組
   - 實現狀態轉移
   - 處理邊界情況

## 建議程式碼實現
```python
def solution(self, n: int) -> int:
    # DP 數組初始化
    dp = [0] * (n + 1)
    
    # 基礎情況
    dp[0] = 0
    dp[1] = 1
    
    # 狀態轉移
    for i in range(2, n + 1):
        # TODO: 實現狀態轉移方程
        pass
        
    return dp[n]
```

## 複雜度分析
- 時間複雜度：O(n) - 需要遍歷 n 個狀態
- 空間複雜度：O(n) - 需要 DP 數組儲存狀態

## 優化建議
1. 考慮空間優化（滾動數組）
2. 注意狀態轉移順序
3. 可能的記憶化搜索優化
"""

    def _generate_default_solution(self, info: Dict) -> str:
        return f"""## 解題分析
針對 {info['title']} 這個{info['difficulty']}難度的問題，我們需要：
1. 仔細理解問題要求
2. 設計高效的解決方案
3. 注意邊界情況處理

## 解題思路
1. 基本思路：
   - 分析輸入數據特點
   - 確定核心算法策略
   - 考慮效能優化
   
2. 實現步驟：
   - 處理特殊情況
   - 實現主要邏輯
   - 優化和測試

## 建議程式碼實現
```python
def solution(self) -> None:
    # TODO: 根據具體問題實現解決方案
    pass
```

## 複雜度分析
- 時間複雜度：需要根據具體實現分析
- 空間複雜度：需要根據具體實現分析

## 優化建議
1. 考慮更高效的數據結構
2. 注意代碼的可讀性和維護性
3. 添加適當的註釋和文檔
"""

    def update_note_content(self, file_path: str) -> None:
        """更新筆記內容"""
        try:
            # 讀取原始筆記
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取題目信息
            problem_info = self.extract_problem_info(content)
            
            # 生成解題思路
            solution = self.generate_solution_template(problem_info)
            
            # 更新筆記內容
            updated_content = re.sub(
                r'## 建議解題思路.*?### 相關延伸學習',
                f'{solution}\n\n### 相關延伸學習',
                content,
                flags=re.DOTALL
            )
            
            # 保存更新後的筆記
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            self.logger.info(f"成功更新筆記: {file_path}")
            
        except Exception as e:
            self.logger.error(f"更新筆記失敗: {e}")

    def monitor_and_update(self, notes_dir: str) -> None:
        """監控並更新新的筆記"""
        try:
            # 獲取當前工作目錄
            current_dir = Path.cwd()
            notes_path = current_dir / notes_dir
            self.logger.info(f"正在檢查目錄: {notes_path}")
            
            if not notes_path.exists():
                self.logger.error(f"目錄不存在: {notes_path}")
                return
            
            # 獲取最新的筆記
            notes = list(notes_path.glob("note_*.md"))
            self.logger.info(f"找到 {len(notes)} 個筆記文件")
            
            if not notes:
                self.logger.info("沒有找到筆記文件")
                return
            
            # 打印所有找到的筆記文件
            for note in notes:
                self.logger.info(f"找到筆記: {note}")
            
            latest_note = max(notes, key=lambda x: x.stat().st_mtime)
            self.logger.info(f"最新筆記: {latest_note}")
            
            # 讀取並打印筆記內容
            try:
                with open(latest_note, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.logger.info(f"成功讀取筆記內容，長度: {len(content)}")
            except Exception as e:
                self.logger.error(f"讀取筆記失敗: {e}")
                return
            
            # 更新筆記
            self.update_note_content(str(latest_note))
            self.logger.info("完成筆記更新")
            
        except Exception as e:
            self.logger.error(f"監控更新失敗: {e}")
            raise
            
if __name__ == "__main__":
    updater = SolutionUpdater()
    updater.monitor_and_update("learning_notes")
