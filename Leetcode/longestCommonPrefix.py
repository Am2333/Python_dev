# 编写一个函数来查找字符串数组中的最长公共前缀。

# 如果不存在公共前缀，返回空字符串 ""。

 

# 示例 1：

# 输入：strs = ["flower","flow","flight"]
# 输出："fl"
# 示例 2：

# 输入：strs = ["dog","racecar","car"]
# 输出：""
# 解释：输入不存在公共前缀。
class Solution(object):
    def longestCommonPrefix(self, strs):
        """
        :type strs: List[str]
        :rtype: str
        """
        #思路为嵌套循环，两两比较，然后存储一个公共字符串，再与后面比较，这个过程中，公共字符串的长度只会不变或者越来越短
        prefix,count = strs[0],len(strs)
        for i in range(0,count):
            
            index = 0
            # for index in range(0,min(len(prefix),len(strs[i]))):
            min_len = min(len(prefix),len(strs[i]))
            while index < min_len and prefix[index] == strs[i][index]:
                if prefix[index] == strs[i][index]:
                    index += 1
            prefix = prefix[:index]
            if not prefix:
                break
        return prefix

strs = ["flower","flow","flight"]
solution = Solution()  # 创建类的实例
print(solution.longestCommonPrefix(strs))
    #还有另一种方法，上面为嵌套循环横向遍历，也可以通过将所有字符串的首字母一排列出，然后一列一列的check，来输出最长公共字符串
    # def longestCommonPrefix(self, strs: List[str]) -> str:
    #     if not strs:
    #         return ""
        
    #     prefix, count = strs[0], len(strs)
    #     for i in range(1, count):
    #         prefix = self.lcp(prefix, strs[i])
    #         if not prefix:
    #             break
        
    #     return prefix

    # def lcp(self, str1, str2):
    #     length, index = min(len(str1), len(str2)), 0
    #     while index < length and str1[index] == str2[index]:
    #         index += 1
    #     return str1[:index]