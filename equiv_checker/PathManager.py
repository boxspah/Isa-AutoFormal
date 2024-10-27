from joblib import Parallel, delayed  
from multiprocessing import Value, Lock  
  
class PathManager:  
    def __init__(self, file_paths, manager):  
        self.file_paths = file_paths  
        self.index = manager.Value('i', 0)  # 用于跟踪当前文件路径索引的共享计数器  
        self.lock = manager.Lock()  # 锁，用于保护对索引的访问  
  
    def get_next_path(self):  
        with self.lock:  
            if self.index.value >= len(self.file_paths):  
                return None  # 所有路径都已处理完毕  
            path = self.file_paths[self.index.value]  # 获取当前索引的文件路径  
            self.index.value += 1  # 索引递增  
            return path
        
    def get_index(self):
        return self.index