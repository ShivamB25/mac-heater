import numpy as np

class MatrixCalculator:
    def __init__(self, size=500):
        self.size = size
        
    def generate_matrices(self):
        return (np.random.rand(self.size, self.size),
                np.random.rand(self.size, self.size))
    
    def heavy_calculation(self, matrix_a, matrix_b):
        try:
            # Matrix multiplication
            result = np.dot(matrix_a, matrix_b)
            
            # Additional operations to increase CPU load
            for _ in range(3):
                result = np.dot(result, result)
                result = np.linalg.matrix_power(result, 2)
                result = np.exp(result / np.max(result))
                
            # Force computation
            result = np.abs(result)
            _ = np.sum(result)
            
            return result
        except:
            return None